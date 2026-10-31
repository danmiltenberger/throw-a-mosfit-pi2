import RPi.GPIO as GPIO #type: ignore
import time

### button pins
start_match = 26
start_kick = 19
change_team = 13
change_goal = 6
end = 5



# dictionary keys
OUR_TEAM_COLOR = "OUR_TEAM_COLOR"
OUR_LEFT_GOAL = "OUR_LEFT_GOAL"
HEADER_ROW = "HEADER_ROW"
BUTTON_STATUS = "BUTTON_STATUS"

# dict vals
GOAL_GREEN = "GRE"
GOAL_PURPLE = "PUR"
TEAM_YELLOW = "YEL"
TEAM_BLUE = "BLU"

HEADER_WAITING = "Change settings or start"

status_str = "not read"

match_settings = {
    OUR_LEFT_GOAL : GOAL_GREEN,
    OUR_TEAM_COLOR : TEAM_YELLOW,
    HEADER_ROW : HEADER_WAITING,
    BUTTON_STATUS : status_str,
}



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


def get_button_status_str(button_status: dict) -> str:
    status_m = "M" + str(int(button_status[start_match]))
    status_p = "P" + str(int(button_status[start_kick]))
    status_t = "T" + str(int(button_status[change_team])) 
    status_g = "G" + str(int(button_status[change_goal]))
    status_x = "X" + str(int(button_status[end]))

    status_str = status_m + "_" + status_p + "_" + status_t + "_" + status_g + "_" + status_x
    return status_str


def get_lcd_rows_button_status(button_status: dict) -> list[str]:
    row1 = "Waiting for input"
    row2 = "M" + str(int(button_status[start_match])) + "_P" + str(int(button_status[start_kick]))
    row3 = "T" + str(int(button_status[change_team])) + "_G" + str(int(button_status[change_goal]))
    row4 = "Exit:" + str(int(button_status[end]))

    return [row1, row2, row3, row4]


def get_lcd_rows_match_settings(match_settings: dict) -> list[str]:
    row1 = match_settings[HEADER_ROW]
    row2 = f"US: {match_settings[OUR_TEAM_COLOR]}, LEFT: {match_settings[OUR_LEFT_GOAL]}"
    row3 = match_settings[BUTTON_STATUS]

    return [row1, row2, row3]