import RPi.GPIO as GPIO  # type: ignore
from picamera2 import Picamera2 #type: ignore

from run_penalty_kick import penalty
from run_match import one_v_one_match
from tam_lcd import write_lcd_lines
from tam_constants import (
    CAMERA_CAPTURE_X, 
    CAMERA_CAPTURE_Y,
    START_KICK_PIN,
    START_MATCH_PIN,
    CHANGE_GOAL_PIN,
    CHANGE_TEAM_PIN,
    END_GAME_PIN,
    match_settings,
    BUTTON_STATUS,
    OUR_LEFT_GOAL,
    GOAL_GREEN,
    GOAL_PURPLE,
    OUR_TEAM_COLOR,
    TEAM_BLUE,
    TEAM_YELLOW,
    
)
from tam_buttons import (
    get_button_status_str,
    get_button_status,
    get_lcd_rows_match_settings
)


def menu():

    print("setting up pins")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(START_MATCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(START_KICK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CHANGE_TEAM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CHANGE_GOAL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(END_GAME_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


    # Create once at program startup
    print("setting up picam")
    picam2 = Picamera2()

    # RGB888 gives an OpenCV-compatible 3-channel image
    config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y)}
    )
    picam2.configure(config)
    picam2.start()

    our_left_is_purple = False
    our_team_is_blue = False

    print("entering menu, press buttons to choose a setting")
    try:
        while True:
            button_status = get_button_status()

            match_settings[BUTTON_STATUS] = get_button_status_str(button_status)

            if button_status[CHANGE_GOAL_PIN]:

                # if our left was purple, it's now green
                if our_left_is_purple:
                    match_settings[OUR_LEFT_GOAL] = GOAL_GREEN

                # or if our left was green, now it's purple
                else:
                    match_settings[OUR_LEFT_GOAL] = GOAL_PURPLE

                # either way, the state has swapped
                our_left_is_purple = not our_left_is_purple

            if button_status[CHANGE_TEAM_PIN]:
                if our_team_is_blue:
                    match_settings[OUR_TEAM_COLOR] = TEAM_YELLOW
                else:
                    match_settings[OUR_TEAM_COLOR] = TEAM_BLUE
                our_team_is_blue = not our_team_is_blue

            if button_status[START_KICK_PIN]:
                penalty(match_settings, picam2)

            if button_status[START_MATCH_PIN]:
                one_v_one_match(match_settings, picam2)

            list_settings = get_lcd_rows_match_settings(match_settings)
            write_lcd_lines(list_settings)

    except KeyboardInterrupt:
        write_lcd_lines(["Program Quit","python main.py"])
        pass
    finally:
        write_lcd_lines([])
        GPIO.cleanup()


if __name__ == "__main__":
    menu()
