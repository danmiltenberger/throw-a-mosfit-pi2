"""
read_sonar_in(): HC-SR04 on a Raspberry Pi 5 using lgpio directly,
with the gpiochip number set explicitly (needed when /dev/gpiochip0 doesn't exist).

Wiring (ECHO must go through the BD-LLC level converter: it outputs 5 V):
    HC-SR04 TRIG -> BD-LLC HV1 ... LV1 -> GPIO23 (pin 16)
    HC-SR04 ECHO -> BD-LLC HV2 ... LV2 -> GPIO24 (pin 18)

Setup:
    sudo apt install python3-lgpio
    gpiodetect        # use the number of the chip labeled pinctrl-rp1
"""

import time

import lgpio

GPIO_CHIP = 15      # the "pinctrl-rp1" chip from gpiodetect on your Pi
TRIG_PIN = 23       # BCM numbering
ECHO_PIN = 24
TIMEOUT_S = 0.03
_INCHES_PER_S = 343.0 * 39.3701

_h = None


def _setup():
    global _h
    _h = lgpio.gpiochip_open(GPIO_CHIP)
    lgpio.gpio_claim_output(_h, TRIG_PIN, 0)
    lgpio.gpio_claim_input(_h, ECHO_PIN)
    time.sleep(0.1)


def read_sonar_in():
    """Distance in inches, or None if no echo. Wait ~60 ms between calls."""
    if _h is None:
        _setup()

    lgpio.gpio_write(_h, TRIG_PIN, 1)
    time.sleep(0.00001)
    lgpio.gpio_write(_h, TRIG_PIN, 0)

    deadline = time.perf_counter() + TIMEOUT_S
    while lgpio.gpio_read(_h, ECHO_PIN) == 0:
        if time.perf_counter() > deadline:
            return None
    start = time.perf_counter()

    deadline = start + TIMEOUT_S
    while lgpio.gpio_read(_h, ECHO_PIN) == 1:
        if time.perf_counter() > deadline:
            return None
    pulse = time.perf_counter() - start

    return pulse * _INCHES_PER_S / 2.0


def close_sonar():
    """Release the GPIO pins."""
    global _h
    if _h is not None:
        lgpio.gpiochip_close(_h)
        _h = None


if __name__ == "__main__":
    print("Reading HC-SR04 (Ctrl+C to stop)")
    try:
        while True:
            dist = read_sonar_in()
            print("Distance: {:6.1f} in".format(dist) if dist is not None else "Distance: no echo")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        close_sonar()