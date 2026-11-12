import RPi.GPIO as GPIO #type: ignore
import time

switch_pin_team_color = 26
switch_pin_goal_color = 19
switch_pin_match_type = 13
switch_pin_recording = 6

SWITCHES = {
    "Team Color": switch_pin_team_color,
    "Goal Color": switch_pin_goal_color,
    "Match Type": switch_pin_match_type,
    "Recording":  switch_pin_recording,
}


def setup_switches():
    GPIO.setmode(GPIO.BCM)
    for pin in SWITCHES.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def print_switch_status():
    """Read and print the state of each switch once."""
    print("-" * 30)
    for name, pin in SWITCHES.items():
        # With pull-up wiring: LOW (0) = switch closed = ON
        state = "ON" if GPIO.input(pin) == GPIO.LOW else "OFF"
        print(f"{name:<12} (GPIO {pin:>2}): {state}")


if __name__ == "__main__":
    setup_switches()
    try:
        while True:
            print_switch_status()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        GPIO.cleanup()