from I2C_write import write_lcd_lines
from datetime import datetime
import RPi.GPIO as GPIO #type: ignore
import time


start_match = 26
start_kick = 19
change_team = 13
change_goal = 6
end = 5


# dictionary keys
OUR_TEAM_COLOR = "OUR_TEAM_COLOR"
OUR_LEFT_GOAL = "OUR_LEFT_GOAL"
HEADER_ROW = "HEADER_ROW"

# dict vals
GOAL_GREEN = "GRE"
GOAL_PURPLE = "PUR"
TEAM_YELLOW = "YEL"
TEAM_BLUE = "BLU"

HEADER_WAITING = "Change settings or start"
BUTTON_STATUS = "BUTTON_STATUS"

status_str = "no read"

match_settings = {
    OUR_LEFT_GOAL : GOAL_GREEN,
    OUR_TEAM_COLOR : TEAM_YELLOW,
    HEADER_ROW : HEADER_WAITING,
    BUTTON_STATUS : status_str,
}




def demo_buttons():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(start_match, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(start_kick, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(change_team, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(change_goal, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(end, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
                pretend_penalty(match_settings)

            if button_status[start_match]:
                pretend_match(match_settings)


            print_to_lcd_match_settings(match_settings)


    except KeyboardInterrupt:
        pass
    finally:
        write_lcd_lines([])
        GPIO.cleanup()

def get_status_str(button_status: dict) -> str:
    status_m = "M" + str(int(button_status[start_match]))
    status_p = "P" + str(int(button_status[start_kick]))
    status_t = "T" + str(int(button_status[change_team])) 
    status_g = "G" + str(int(button_status[change_goal]))
    status_x = "X" + str(int(button_status[end]))

    status_str = status_m + "_" + status_p + "_" + status_t + "_" + status_g + "_" + status_x
    return status_str


def pretend_match(match_settings):

    time_start = time.perf_counter()
    while True:
        button_status = get_button_status()
        match_settings[BUTTON_STATUS] = get_status_str(button_status)
        if button_status[end]:
            return

        time_current = time.perf_counter()
        time_elapsed = str(round(time_current - time_start,2))

        row1 = f"Match! {time_elapsed}"
        row2 = f"US: {match_settings[OUR_TEAM_COLOR]}, LEFT: {match_settings[OUR_LEFT_GOAL]}"


        row4 = match_settings[BUTTON_STATUS]

        write_lcd_lines([row1,row2,row4])


def pretend_penalty(match_settings):

    time_start = time.perf_counter()
    while True:
        button_status = get_button_status()
        match_settings[BUTTON_STATUS] = get_status_str(button_status)
        if button_status[end]:
            return

        time_current = time.perf_counter()
        time_elapsed = str(round(time_current - time_start,2))

        row1 = f"Penalty! {time_elapsed}"
        row2 = f"US: {match_settings[OUR_TEAM_COLOR]}, LEFT: {match_settings[OUR_LEFT_GOAL]}"


        row4 = match_settings[BUTTON_STATUS]

        write_lcd_lines([row1,row2,row4])



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
    row2 = "M" + str(int(button_status[start_match])) + "_P" + str(int(button_status[start_kick]))
    row3 = "T" + str(int(button_status[change_team])) + "_G" + str(int(button_status[change_goal]))
    row4 = "Exit:" + str(int(button_status[end]))

    write_lcd_lines([
        row1, row2, row3, row4
    ])


def print_to_lcd_match_settings(match_settings: dict):
    row1 = match_settings[HEADER_ROW]
    row2 = f"US: {match_settings[OUR_TEAM_COLOR]}, LEFT: {match_settings[OUR_LEFT_GOAL]}"
    row3 = match_settings[BUTTON_STATUS]
    write_lcd_lines([row1, row2, row3])


if __name__ == "__main__":
    demo_buttons()