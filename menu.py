from I2C_write import write_lcd_lines
from datetime import datetime
import RPi.GPIO as GPIO  # type: ignore
from picamera2 import Picamera2 #type: ignore
import time
from penalty_kick import penalty
from play_match import one_v_one_match
from constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y
from menu_constants import (
    start_match,
    start_kick,
    status_str,
    change_team,
    change_goal,
    match_settings,
    BUTTON_STATUS,
    end,
    OUR_LEFT_GOAL,
    OUR_TEAM_COLOR,
    GOAL_GREEN,
    GOAL_PURPLE,
    TEAM_BLUE,
    TEAM_YELLOW,
    HEADER_ROW,
    HEADER_WAITING,
    get_status_str,
    get_button_status,
    print_to_lcd_match_settings
)


def menu():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(start_match, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(start_kick, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(change_team, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(change_goal, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(end, GPIO.IN, pull_up_down=GPIO.PUD_UP)


    # Create once at program startup
    picam2 = Picamera2()

    # RGB888 gives an OpenCV-compatible 3-channel image
    config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y)}
    )
    picam2.configure(config)
    picam2.start()

    our_left_is_purple = False
    our_team_is_blue = False

    try:
        while True:
            button_status = get_button_status()

            match_settings[BUTTON_STATUS] = get_status_str(button_status)

            if button_status[change_goal]:

                # if our left was purple, it's now green
                if our_left_is_purple:
                    match_settings[OUR_LEFT_GOAL] = GOAL_GREEN

                # or if our left was green, now it's purple
                else:
                    match_settings[OUR_LEFT_GOAL] = GOAL_PURPLE

                # either way, the state has swapped
                our_left_is_purple = not our_left_is_purple

            if button_status[change_team]:
                if our_team_is_blue:
                    match_settings[OUR_TEAM_COLOR] = TEAM_YELLOW
                else:
                    match_settings[OUR_TEAM_COLOR] = TEAM_BLUE
                our_team_is_blue = not our_team_is_blue

            if button_status[start_kick]:
                penalty(match_settings, picam2)

            if button_status[start_match]:
                one_v_one_match(match_settings, picam2)

            print_to_lcd_match_settings(match_settings)

    except KeyboardInterrupt:
        pass
    finally:
        write_lcd_lines([])
        GPIO.cleanup()


if __name__ == "__main__":
    menu()
