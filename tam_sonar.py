"""
read_sonar_in(): read an HC-SR04 ultrasonic sensor on a Raspberry Pi 5.

Wiring (ECHO must go through the BD-LLC level converter: it outputs 5 V):
    HC-SR04 VCC  -> Pi 5V (pin 2 or 4)
    HC-SR04 GND  -> Pi GND
    HC-SR04 TRIG -> BD-LLC HV1 ... LV1 -> GPIO23 (pin 16)
    HC-SR04 ECHO -> BD-LLC HV2 ... LV2 -> GPIO24 (pin 18)
    BD-LLC HV -> 5V, LV -> 3.3V, GND -> GND

Setup:
    pip install gpiozero lgpio
"""

import time

from gpiozero import DistanceSensor

TRIG_PIN = 23
ECHO_PIN = 24
MAX_DISTANCE_M = int(4.0)
_IN_PER_M = 39.3701

_sensor = None


def read_sonar_in():
    """
    Return the distance to the nearest object in inches,
    or None if nothing was detected within range (~0.8 to 157 in).
    The sensor is set up on the first call.
    """
    global _sensor
    if _sensor is None:
        _sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN, max_distance=MAX_DISTANCE_M)

    d = _sensor.distance  # meters; clamps to max_distance when there is no echo
    if d >= MAX_DISTANCE_M:
        return None
    return d * _IN_PER_M


def close_sonar():
    """Release the GPIO pins."""
    global _sensor
    if _sensor is not None:
        _sensor.close()
        _sensor = None


if __name__ == "__main__":
    print("Reading HC-SR04 (Ctrl+C to stop)")
    try:
        while True:
            dist = read_sonar_in()
            print("Distance: {:6.1f} in".format(dist) if dist is not None else "Distance: out of range")
            time.sleep(0.1)  # HC-SR04 needs ~60 ms between pings
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        close_sonar()