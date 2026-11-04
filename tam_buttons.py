import RPi.GPIO as GPIO  # type: ignore
import time
from tam_constants import (
    status_str,
    match_settings,
    BUTTON_STATUS,
    OUR_LEFT_GOAL,
    OUR_TEAM_COLOR,
    GOAL_GREEN,
    GOAL_PURPLE,
    TEAM_BLUE,
    TEAM_YELLOW,
    HEADER_ROW,
    HEADER_WAITING,
    START_MATCH_PIN,
    START_KICK_PIN,
    CHANGE_GOAL_PIN,
    CHANGE_TEAM_PIN,
    END_GAME_PIN
)



def get_button_status() -> dict:
    button_status: dict = {
        START_MATCH_PIN: False,
        START_KICK_PIN: False,
        CHANGE_TEAM_PIN: False,
        CHANGE_GOAL_PIN: False,
        END_GAME_PIN: False,
    }

    if GPIO.input(START_MATCH_PIN) == GPIO.LOW:
        button_status[START_MATCH_PIN] = True
        time.sleep(0.2)

    if GPIO.input(START_KICK_PIN) == GPIO.LOW:
        button_status[START_KICK_PIN] = True
        time.sleep(0.2)

    if GPIO.input(CHANGE_TEAM_PIN) == GPIO.LOW:
        button_status[CHANGE_TEAM_PIN] = True
        time.sleep(0.2)

    if GPIO.input(CHANGE_GOAL_PIN) == GPIO.LOW:
        button_status[CHANGE_GOAL_PIN] = True
        time.sleep(0.2)

    if GPIO.input(END_GAME_PIN) == GPIO.LOW:
        button_status[END_GAME_PIN] = True
        time.sleep(0.2)

    return button_status


def get_button_status_str(button_status: dict) -> str:
    status_m = "M" + str(int(button_status[START_MATCH_PIN]))
    status_p = "P" + str(int(button_status[START_KICK_PIN]))
    status_t = "T" + str(int(button_status[CHANGE_TEAM_PIN]))
    status_g = "G" + str(int(button_status[CHANGE_GOAL_PIN]))
    status_x = "X" + str(int(button_status[END_GAME_PIN]))

    status_str = (
        status_m + "_" + status_p + "_" + status_t + "_" + status_g + "_" + status_x
    )
    return status_str


def get_lcd_rows_button_status(button_status: dict) -> list[str]:
    row1 = "Waiting for input"
    row2 = (
        "M"
        + str(int(button_status[START_MATCH_PIN]))
        + "_P"
        + str(int(button_status[START_KICK_PIN]))
    )
    row3 = (
        "T"
        + str(int(button_status[CHANGE_TEAM_PIN]))
        + "_G"
        + str(int(button_status[CHANGE_GOAL_PIN]))
    )
    row4 = "Exit:" + str(int(button_status[END_GAME_PIN]))

    return [row1, row2, row3, row4]


def get_lcd_rows_match_settings(match_settings: dict) -> list[str]:
    row1 = match_settings[HEADER_ROW]
    row2 = (
        f"US: {match_settings[OUR_TEAM_COLOR]}, LEFT: {match_settings[OUR_LEFT_GOAL]}"
    )
    row3 = match_settings[BUTTON_STATUS]

    return [row1, row2, row3]
