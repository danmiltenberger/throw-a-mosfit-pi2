### easily test the switches

from tam_switches import get_switch_status, setup_switches, SWITCHES
from tam_lcd import write_lcd_lines
from tam_draw import format_lcd_line



setup_switches()
while True:


    try:
        status_match = get_switch_status(switch_name="toggle_match_type")
        status_team = get_switch_status(switch_name="toggle_team")
        status_goal = get_switch_status(switch_name="toggle_goal")
        status_recording = get_switch_status(switch_name="toggle_recording")
        status_send_commands = get_switch_status(switch_name="toggle_arduino_commands")

        row1 = f"Match: {int(status_match)} " + f"Team: {int(status_team)}"
        row2 = f"Goal:  {int(status_goal)} " +  f"Rec:  {int(status_recording)}"
        row3 = f"Send Com: {int(status_send_commands)}"


        list_lines = [row1, row2, row3]
        write_lcd_lines(list_lines)
    except KeyboardInterrupt:
        write_lcd_lines(["No Program"])
        break

    