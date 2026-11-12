import RPi.GPIO as GPIO  # type: ignore
from tam_pins import END_GAME_PIN, START_KICK_PIN, START_MATCH_PIN, CHANGE_GOAL_PIN, CHANGE_TEAM_PIN
from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_buttons import get_button_status
from tam_classes import Settings

def main():

    # setup switches and buttons
    setup_pins()

    # setup cameras
    camL, camR = setup_left_right_cams()

    # get the default settings
    settings = Settings()

    # continually update our position and field understanding
    while True:

        # read status of the buttons and update settings if needed
        button_dict = get_button_status()
        settings = update_settings_with_buttons(settings, button_dict)

        # always look through the cameras 
        frameL, frameR = get_left_right_frames(cam_left=camL, cam_right= camR)

        





def update_settings_with_buttons(settings: Settings, button_dict: dict[int,bool]) -> Settings:
    '''read the button states and update the settings class, changing our team color and goal color'''

    if button_dict[CHANGE_GOAL_PIN] == True:
        settings.west_goalpost_is_green = not settings.west_goalpost_is_green

    if button_dict[CHANGE_TEAM_PIN] == True:
        settings.our_team_is_yellow = not settings.our_team_is_yellow

    return settings


def setup_pins():
    print("setting up pins")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(START_MATCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(START_KICK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CHANGE_TEAM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CHANGE_GOAL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(END_GAME_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)



if __name__ == "__main__":
    main()