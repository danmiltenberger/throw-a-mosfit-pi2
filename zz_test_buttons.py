from I2C_write import write_lcd_lines
from datetime import datetime
import RPi.GPIO as GPIO
import time


first_button_pin = 3
second_button_pin = 4
third_button_pin = 5
fourth_button_pin = 6
fifth_button_pin = 7


now = datetime.now()
time_str = now.strftime("%Y-%m-%d %H:%M:%S")



first_button_pin = 17  # BCM GPIO number

def check_button():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(first_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(second_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(third_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(fourth_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(fifth_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        while True:

            button_status = ""

            if GPIO.input(first_button_pin) == GPIO.LOW:
                print("button 1 pressed")
                button_status = "one"
                time.sleep(0.2)  # simple debounce

            if GPIO.input(second_button_pin) == GPIO.LOW:
                print("button 2 pressed")
                time.sleep(0.2)  # simple debounce
                button_status = "two"

            if GPIO.input(third_button_pin) == GPIO.LOW:
                print("button 3 pressed")
                time.sleep(0.2)  # simple debounce
                button_status = "three"

            if GPIO.input(fourth_button_pin) == GPIO.LOW:
                print("button 4 pressed")
                time.sleep(0.2)  # simple debounce
                button_status = "four"

            if GPIO.input(fifth_button_pin) == GPIO.LOW:
                print("button 5 pressed")
                time.sleep(0.2)  # simple debounce
                button_status = "five"

            write_lcd_lines([
                "waiting for buttons",

            ])



    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    check_button()