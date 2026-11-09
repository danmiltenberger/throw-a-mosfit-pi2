import time
from tam_buttons import BUTTON_STATUS, get_button_status_str, get_button_status, OUR_LEFT_GOAL, OUR_TEAM_COLOR, END_GAME_PIN
from tam_lcd import write_lcd_lines
from tam_arduino import send_command_to_arduino
from tam_classes import BotCommand
from tam_commands import BOT_FORWARD

def penalty(match_settings, picam):

    time_start = time.perf_counter()
    while True:
        button_status = get_button_status()
        match_settings[BUTTON_STATUS] = get_button_status_str(button_status)
        if button_status[END_GAME_PIN]:
            return

        time_current = time.perf_counter()
        time_elapsed = str(round(time_current - time_start,2))

        row1 = f"Penalty! {time_elapsed}"
        row2 = f"US: {match_settings[OUR_TEAM_COLOR]}, LEFT: {match_settings[OUR_LEFT_GOAL]}"


        bot_command = BotCommand(BOT_FORWARD, 3)
        send_command_to_arduino(command=bot_command)


        row4 = match_settings[BUTTON_STATUS]

        write_lcd_lines([row1,row2,row4])