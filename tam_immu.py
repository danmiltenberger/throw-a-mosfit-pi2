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

import math
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


# ---------------------------------------------------------------------------
# Pose estimation
# ---------------------------------------------------------------------------
_IN_PER_G = _G * 39.3701          # 1 g in inches/s^2
_WARMUP_S = 2.0                   # let the attitude filter converge; keep still
_pose = None


def reset_pose():
    """Forget the current pose; the next update_pose() call re-zeros position and re-converges."""
    global _pose
    _pose = None


def update_pose(imu, use_mag=True):
    """
    Dead-reckon position and heading from a read_immu() sample.
    Call this repeatedly (e.g. every 10-20 ms) with fresh read_immu() output.

    Returns a dict:
        pos_in      : (north, east, up) in inches, relative to where it started
        bearing_deg : heading, 0-360, clockwise (0 = magnetic north if the mag is used,
                      otherwise 0 = the heading at startup)
        vel_in_s    : (north, east, up) in inches/second
        roll_deg, pitch_deg, stationary, ready

    Keep the IMU still for the first ~2 s ('ready' becomes True after that).
    Position is double-integrated accelerometer data, so it WILL drift; a
    zero-velocity update (ZUPT) resets velocity whenever the IMU sits still.
    """
    global _pose
    now = time.monotonic()
    if _pose is None:
        _pose = {"q": [1.0, 0.0, 0.0, 0.0], "v": [0.0, 0.0, 0.0], "p": [0.0, 0.0, 0.0],
                 "bias": [0.0, 0.0, 0.0], "t": now, "t0": now, "still": 0}
    s = _pose
    dt = min(max(now - s["t"], 0.0), 0.5)
    s["t"] = now
    warm = (now - s["t0"]) < _WARMUP_S

    ax, ay, az = imu["accel_g"]
    gdps = imu["gyro_dps"]
    amag = math.sqrt(ax * ax + ay * ay + az * az)

    # --- stationary detection + gyro bias tracking ---
    gmag = math.sqrt(sum((g - b) ** 2 for g, b in zip(gdps, s["bias"])))
    stationary = abs(amag - 1.0) < 0.04 and gmag < 5.0
    s["still"] = s["still"] + 1 if stationary else 0
    if stationary:
        s["bias"] = [b + 0.05 * (g - b) for g, b in zip(gdps, s["bias"])]
    gx, gy, gz = (math.radians(g - b) for g, b in zip(gdps, s["bias"]))

    # --- Mahony attitude filter (q = body -> world; world: x north, y west, z up) ---
    q0, q1, q2, q3 = s["q"]
    ex = ey = ez = 0.0

    if 0.85 < amag < 1.15:  # only trust accel as a gravity reference when not accelerating
        nx, ny, nz = ax / amag, ay / amag, az / amag
        vx = 2 * (q1 * q3 - q0 * q2)
        vy = 2 * (q0 * q1 + q2 * q3)
        vz = q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3
        ex += ny * vz - nz * vy
        ey += nz * vx - nx * vz
        ez += nx * vy - ny * vx

    mag = imu.get("mag_ut") if use_mag else None
    if mag:
        mx, my, mz = mag[1], mag[0], -mag[2]  # AK8963 axes -> accel/gyro axes
        mn = math.sqrt(mx * mx + my * my + mz * mz)
        if mn > 0:
            mx, my, mz = mx / mn, my / mn, mz / mn
            hx = 2 * (mx * (0.5 - q2 * q2 - q3 * q3) + my * (q1 * q2 - q0 * q3) + mz * (q1 * q3 + q0 * q2))
            hy = 2 * (mx * (q1 * q2 + q0 * q3) + my * (0.5 - q1 * q1 - q3 * q3) + mz * (q2 * q3 - q0 * q1))
            hz = 2 * (mx * (q1 * q3 - q0 * q2) + my * (q2 * q3 + q0 * q1) + mz * (0.5 - q1 * q1 - q2 * q2))
            bx, bz = math.sqrt(hx * hx + hy * hy), hz
            wx = 2 * (bx * (0.5 - q2 * q2 - q3 * q3) + bz * (q1 * q3 - q0 * q2))
            wy = 2 * (bx * (q1 * q2 - q0 * q3) + bz * (q0 * q1 + q2 * q3))
            wz = 2 * (bx * (q0 * q2 + q1 * q3) + bz * (0.5 - q1 * q1 - q2 * q2))
            ex += my * wz - mz * wy
            ey += mz * wx - mx * wz
            ez += mx * wy - my * wx

    kp = 10.0 if warm else 1.0
    gx, gy, gz = gx + kp * ex, gy + kp * ey, gz + kp * ez

    h = 0.5 * dt
    q0, q1, q2, q3 = (q0 + (-q1 * gx - q2 * gy - q3 * gz) * h,
                      q1 + (q0 * gx + q2 * gz - q3 * gy) * h,
                      q2 + (q0 * gy - q1 * gz + q3 * gx) * h,
                      q3 + (q0 * gz + q1 * gy - q2 * gx) * h)
    n = math.sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
    q0, q1, q2, q3 = q0 / n, q1 / n, q2 / n, q3 / n
    s["q"] = [q0, q1, q2, q3]

    # --- rotate accel into the world frame, remove gravity, integrate ---
    wxa = (1 - 2 * (q2 * q2 + q3 * q3)) * ax + 2 * (q1 * q2 - q0 * q3) * ay + 2 * (q1 * q3 + q0 * q2) * az
    wya = 2 * (q1 * q2 + q0 * q3) * ax + (1 - 2 * (q1 * q1 + q3 * q3)) * ay + 2 * (q2 * q3 - q0 * q1) * az
    wza = 2 * (q1 * q3 - q0 * q2) * ax + 2 * (q2 * q3 + q0 * q1) * ay + (1 - 2 * (q1 * q1 + q2 * q2)) * az
    lin = (wxa * _IN_PER_G, wya * _IN_PER_G, (wza - 1.0) * _IN_PER_G)  # in/s^2

    if warm:
        s["v"], s["p"] = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    elif s["still"] >= 5:  # ZUPT
        s["v"] = [0.0, 0.0, 0.0]
    else:
        s["v"] = [v + a * dt for v, a in zip(s["v"], lin)]
        s["p"] = [p + v * dt for p, v in zip(s["p"], s["v"])]

    yaw = math.atan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2 * q2 + q3 * q3))
    roll = math.atan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 * q1 + q2 * q2))
    pitch = math.asin(max(-1.0, min(1.0, 2 * (q0 * q2 - q3 * q1))))
    px, py, pz = s["p"]
    vx_, vy_, vz_ = s["v"]

    return {
        "pos_in": (px, -py, pz),                       # north, east, up
        "bearing_deg": (-math.degrees(yaw)) % 360.0,   # clockwise from north
        "vel_in_s": (vx_, -vy_, vz_),
        "roll_deg": math.degrees(roll),
        "pitch_deg": math.degrees(pitch),
        "stationary": s["still"] >= 5,
        "ready": not warm,
    }


if __name__ == "__main__":
    print("Keep the IMU still for 2 seconds...")
    last_print = 0.0
    while True:
        d = read_immu()
        pose = update_pose(d)
        if time.monotonic() - last_print > 0.2:
            last_print = time.monotonic()
            print("N={:+8.1f} E={:+8.1f} Up={:+8.1f} in | bearing={:6.1f} deg {}".format(
                *pose["pos_in"], pose["bearing_deg"], "" if pose["ready"] else "(calibrating)"))
        time.sleep(0.01)