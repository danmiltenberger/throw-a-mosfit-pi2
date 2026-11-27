"""
read_immu(): read an MPU-9250 / MPU-6500 / MPU-9255 over I2C on a Raspberry Pi 5.

Wiring (I2C bus 1):
    VCC -> 3.3V (pin 1)    GND -> GND (pin 6)
    SDA -> GPIO2 (pin 3)   SCL -> GPIO3 (pin 5)
    AD0 -> GND for address 0x68, or 3.3V for 0x69

Setup:
    sudo raspi-config nonint do_i2c 0      # enable I2C
    pip install smbus2
    i2cdetect -y 1                         # should show 68 (and 0c only after bypass is on)
"""

import struct
import time

from smbus2 import SMBus

# --- MPU registers ---
_WHO_AM_I = 0x75
_PWR_MGMT_1 = 0x6B
_CONFIG = 0x1A
_GYRO_CONFIG = 0x1B
_ACCEL_CONFIG = 0x1C
_INT_PIN_CFG = 0x37
_ACCEL_XOUT_H = 0x3B

# --- AK8963 magnetometer registers (only on 9250/9255) ---
_MAG_ADDR = 0x0C
_MAG_WIA = 0x00
_MAG_ST1 = 0x02
_MAG_XOUT_L = 0x03
_MAG_CNTL1 = 0x0A
_MAG_ASAX = 0x10

_WHO_AM_I_IDS = {0x71: "MPU-9250", 0x73: "MPU-9255", 0x70: "MPU-6500"}

# Full-scale ranges: +/-2 g and +/-250 deg/s
_ACCEL_LSB_PER_G = 16384.0
_GYRO_LSB_PER_DPS = 131.0
_MAG_UT_PER_LSB = 4912.0 / 32760.0  # 16-bit mode, ~0.15 uT/LSB
_G = 9.80665

_state = {"bus": None, "addr": None, "chip": None, "mag_ok": False, "mag_adj": (1.0, 1.0, 1.0)}


def _init(bus_num, addr):
    bus = SMBus(bus_num)

    who = bus.read_byte_data(addr, _WHO_AM_I)
    if who not in _WHO_AM_I_IDS:
        bus.close()
        raise RuntimeError(f"Unexpected WHO_AM_I 0x{who:02X} at 0x{addr:02X}; not an MPU-9250/6500/9255")

    # Reset, then wake with PLL clock
    bus.write_byte_data(addr, _PWR_MGMT_1, 0x80)
    time.sleep(0.1)
    bus.write_byte_data(addr, _PWR_MGMT_1, 0x01)
    time.sleep(0.05)

    bus.write_byte_data(addr, _CONFIG, 0x03)         # gyro/temp DLPF ~41 Hz
    bus.write_byte_data(addr, _GYRO_CONFIG, 0x00)    # +/-250 dps
    bus.write_byte_data(addr, _ACCEL_CONFIG, 0x00)   # +/-2 g

    _state.update(bus=bus, addr=addr, chip=_WHO_AM_I_IDS[who], mag_ok=False)

    # Magnetometer (not present on the MPU-6500)
    if who in (0x71, 0x73):
        try:
            bus.write_byte_data(addr, _INT_PIN_CFG, 0x02)  # I2C bypass -> AK8963 visible at 0x0C
            time.sleep(0.01)
            if bus.read_byte_data(_MAG_ADDR, _MAG_WIA) == 0x48:
                bus.write_byte_data(_MAG_ADDR, _MAG_CNTL1, 0x00)  # power down
                time.sleep(0.01)
                bus.write_byte_data(_MAG_ADDR, _MAG_CNTL1, 0x0F)  # fuse ROM access
                time.sleep(0.01)
                asa = bus.read_i2c_block_data(_MAG_ADDR, _MAG_ASAX, 3)
                _state["mag_adj"] = tuple((a - 128) / 256.0 + 1.0 for a in asa)
                bus.write_byte_data(_MAG_ADDR, _MAG_CNTL1, 0x00)
                time.sleep(0.01)
                bus.write_byte_data(_MAG_ADDR, _MAG_CNTL1, 0x16)  # 16-bit, continuous 100 Hz
                time.sleep(0.01)
                _state["mag_ok"] = True
        except OSError:
            _state["mag_ok"] = False


def read_immu(bus_num=1, addr=0x68):
    """
    Read one sample from the IMU.

    Returns a dict:
        accel_g   : (x, y, z) in g
        accel_ms2 : (x, y, z) in m/s^2
        gyro_dps  : (x, y, z) in deg/s
        mag_ut    : (x, y, z) in microtesla, or None (MPU-6500 / no new data / overflow)
        temp_c    : die temperature in deg C
        chip      : detected chip name
    The bus is opened and the sensor configured on the first call.
    """
    if _state["bus"] is None:
        _init(bus_num, addr)

    bus, addr = _state["bus"], _state["addr"]

    # One burst: accel (3) + temp (1) + gyro (3), big-endian signed 16-bit
    raw = bus.read_i2c_block_data(addr, _ACCEL_XOUT_H, 14)
    ax, ay, az, t, gx, gy, gz = struct.unpack(">7h", bytes(raw))

    accel_g = (ax / _ACCEL_LSB_PER_G, ay / _ACCEL_LSB_PER_G, az / _ACCEL_LSB_PER_G)
    gyro = (gx / _GYRO_LSB_PER_DPS, gy / _GYRO_LSB_PER_DPS, gz / _GYRO_LSB_PER_DPS)
    temp_c = t / 333.87 + 21.0

    mag = None
    if _state["mag_ok"]:
        try:
            if bus.read_byte_data(_MAG_ADDR, _MAG_ST1) & 0x01:  # data ready
                m = bus.read_i2c_block_data(_MAG_ADDR, _MAG_XOUT_L, 8)  # X,Y,Z (little-endian) + ST2
                if not (m[7] & 0x08):  # skip on magnetic overflow
                    mx, my, mz = struct.unpack("<3h", bytes(m[:6]))
                    ax_, ay_, az_ = _state["mag_adj"]
                    mag = (mx * ax_ * _MAG_UT_PER_LSB,
                           my * ay_ * _MAG_UT_PER_LSB,
                           mz * az_ * _MAG_UT_PER_LSB)
        except OSError:
            mag = None

    return {
        "accel_g": accel_g,
        "accel_ms2": tuple(a * _G for a in accel_g),
        "gyro_dps": gyro,
        "mag_ut": mag,
        "temp_c": temp_c,
        "chip": _state["chip"],
    }


if __name__ == "__main__":
    while True:
        d = read_immu()
        print(d["chip"],
              "accel(g)=({:+.3f},{:+.3f},{:+.3f})".format(*d["accel_g"]),
              "gyro(dps)=({:+.1f},{:+.1f},{:+.1f})".format(*d["gyro_dps"]),
              "mag(uT)=" + ("({:+.1f},{:+.1f},{:+.1f})".format(*d["mag_ut"]) if d["mag_ut"] else "n/a"),
              "T={:.1f}C".format(d["temp_c"]))
        time.sleep(0.1)