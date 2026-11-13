import RPi.GPIO as GPIO #type: ignore
import time
from tam_lcd import write_lcd_lines
from dataclasses import dataclass

# color | GPIO pin
pin_brown = 26
pin_red = 19
pin_orange = 13
pin_yellow = 6
pin_green = 5


SWITCHES = {
    "toggle_team" : pin_green,
    "toggle_goal" : pin_yellow,
    "toggle_match_type" : pin_orange,
    "toggle_recording" : pin_red,
    "toggle_arduino_commands" : pin_brown,
}



def setup_switches():
    GPIO.setmode(GPIO.BCM)
    for pin in SWITCHES.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)



def get_switch_status(switch_name) -> bool:
    '''check the status of a switch given the key of the SWITCHES dictionary'''
    switch_pin = SWITCHES[switch_name]

    if GPIO.input(switch_pin):
        return True
    else:
        return False


def get_switches_status_dict() -> dict[str, bool]:
    '''return a dict of key = switch name ie 'toggle_team' and value True or False'''
    switch_dict = {}

    for key in SWITCHES.keys():
        switch_dict[key] = get_switch_status(key)

    return switch_dict



def print_switch_status():
    """Read and print the state of each switch once."""

    print_str = ""

    setup_switches()


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
        str(print_str),
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