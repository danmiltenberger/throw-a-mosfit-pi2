### easily test the switches

from tam_switches import get_switch_status, setup_switches, SWITCHES
from tam_lcd import write_lcd_lines
from tam_draw import format_lcd_line



setup_switches()
while True:



    status_match = get_switch_status(switch_name="toggle_match_type")
    status_team = get_switch_status(switch_name="toggle_team")
    status_goal = get_switch_status(switch_name="toggle_goal")
    status_recording = get_switch_status(switch_name="toggle_recording")
    status_send_commands = get_switch_status(switch_name="toggle_arduino_commands")

    row1_left = f"Match: {int(status_match)}"
    row1_righ = f"Team: {int(status_team)}"
    row2_left = f"Goal: {int(status_goal)}"
    row2_righ = f"Rec: {int(status_recording)}"
    row3 = f"Send Com: {int(status_send_commands)}"

    row1 = format_lcd_line(row1_left,row2_righ)
    row2 = format_lcd_line(row2_left, row2_righ)

    list_lines = [row1, row2, row3]
    write_lcd_lines(list_lines)