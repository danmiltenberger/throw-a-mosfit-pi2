import time
from menu import get_button_status, BUTTON_STATUS, get_status_str, end, OUR_LEFT_GOAL, OUR_TEAM_COLOR
from I2C_write import write_lcd_lines

def match(match_settings: dict):

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