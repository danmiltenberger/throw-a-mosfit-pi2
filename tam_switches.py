import RPi.GPIO as GPIO #type: ignore
import time
from tam_lcd import write_lcd_lines

switch_pin_team_color = 26
switch_pin_goal_color = 19
switch_pin_match_type = 13
switch_pin_recording = 6

# color | pin
pin_brown = 26
pin_red = 19
pin_orange = 13
pin_yellow = 6
pin_green = 5



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

    print_str = ""


    if GPIO.input(pin_green):
        print_str += "g1"
    else:
        print_str += "g0"

    if GPIO.input(pin_yellow):
        print_str += "y1"
    else:
        print_str += "y0"

    if GPIO.input(pin_orange):
        print_str += "o1"
    else:
        print_str += "o0"


    if GPIO.input(pin_red):
        print_str += "r1"
    else:
        print_str += "r0"

    if GPIO.input(pin_brown):
        print_str += "b1"
    else:
        print_str += "b0"

    lines = [
        "Testing switches",
        print_str
    ]

    print(print_str)
    write_lcd_lines(lines)




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