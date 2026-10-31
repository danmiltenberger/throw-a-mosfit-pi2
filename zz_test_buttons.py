from I2C_write import write_lcd_lines
from datetime import datetime
import RPi.GPIO as GPIO
import time


start_match = 26
start_kick = 19
change_team = 13
change_goal = 6
end = 5


def demo_buttons():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(start_match, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(start_kick, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(change_team, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(change_goal, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(end, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        while True:

            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            button_status = ""


            if GPIO.input(start_match) == GPIO.LOW:
                button_status = "start match"
                time.sleep(0.2)  # simple debounce

            if GPIO.input(start_kick) == GPIO.LOW:

                time.sleep(0.2)  # simple debounce
                button_status = "start kick"

            if GPIO.input(change_team) == GPIO.LOW:
                time.sleep(0.2)  # simple debounce
                button_status = "change team"

            if GPIO.input(change_goal) == GPIO.LOW:
                time.sleep(0.2)  # simple debounce
                button_status = "change goal"

            if GPIO.input(end) == GPIO.LOW:
                time.sleep(0.2)  # simple debounce
                button_status = "back to menu"

            write_lcd_lines([
                f"waiting for buttons, {time_str}",
                button_status,

            ])



    except KeyboardInterrupt:
        pass
    finally:
        write_lcd_lines([])
        GPIO.cleanup()

if __name__ == "__main__":
    demo_buttons()