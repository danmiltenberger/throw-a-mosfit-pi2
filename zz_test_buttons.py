from I2C_write import write_lcd_lines
from datetime import datetime
import RPi.GPIO as GPIO #type: ignore
import time


start_match = 5
start_kick = 6
change_team = 13
change_goal = 19
end = 26


def demo_buttons():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(start_match, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(start_kick, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(change_team, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(change_goal, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(end, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        while True:
            button_status = get_button_status()

            print_to_lcd_button_status(button_status)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


def get_button_status() -> dict:
    button_status : dict = {
        start_match : False,
        start_kick : False,
        change_team : False,
        change_goal: False,
        end : False,
    }

    if GPIO.input(start_match) == GPIO.LOW:
        button_status[start_match] = True
        time.sleep(0.2)  

    if GPIO.input(start_kick) == GPIO.LOW:
        button_status[start_kick] = True
        time.sleep(0.2) 


    if GPIO.input(change_team) == GPIO.LOW:
        button_status[change_team] = True
        time.sleep(0.2)

    if GPIO.input(change_goal) == GPIO.LOW:
        button_status[change_goal] = True
        time.sleep(0.2)  

    if GPIO.input(end) == GPIO.LOW:
        button_status[end] = True
        time.sleep(0.2)

    return button_status


def print_to_lcd_button_status(button_status: dict):
    row1 = "Waiting for input"
    row2 = "M" + str(button_status[start_match]) + "_P" + str(button_status[start_kick])
    row3 = "T" + str(button_status[change_team]) + "_G" + str(button_status[change_goal])
    row4 = "Exit:" + str(button_status[end])

    write_lcd_lines([
        row1, row2, row3, row4
    ])


if __name__ == "__main__":
    demo_buttons()