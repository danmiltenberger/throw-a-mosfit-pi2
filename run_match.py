from picamera2 import Picamera2 #type: ignore
from tam_constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y

import time
import cv2
from tam_buttons import *
from tam_frame import get_field_frame
from tam_classes import BotCommand
from tam_vision import get_frame
from tam_frame import save_frame_as_png
from example_stack import vision_full_stack
from tam_lcd import write_lcd_lines

def one_v_one_match(match_settings: dict, picam2):

    save_frame_on_exit : bool = True


    field_frame = get_field_frame(USE_DRAWN_FIELD=False)

    ball_status = "???"
    hat_y_status = "???"
    hat_b_status = "???"
    bot_command = BotCommand()

    time_start = time.perf_counter()
    while True:

        # get each frame
        frame = get_frame(picam2)
        frame_og = frame.copy()

        # check if the program should quit
        button_status = get_button_status()
        match_settings[BUTTON_STATUS] = get_button_status_str(button_status)
        if button_status[end]:

            if save_frame_on_exit:
                save_frame_as_png(frame_og)
            return

        frame_vision_stack = vision_full_stack(frame.copy(), frame_field=field_frame.copy())

        # print information to the LCD
        time_current = time.perf_counter()
        time_elapsed = str(round(time_current - time_start,2))
        row1 = f"Match! {time_elapsed} US: {match_settings[OUR_TEAM_COLOR]}, L: {match_settings[OUR_LEFT_GOAL]}"
        row2 = f"bal {ball_status}, hat_y {hat_y_status} hat_b {hat_b_status}"
        row3 = f"com: {str(bot_command)}"
        row4 = match_settings[BUTTON_STATUS]
        write_lcd_lines([row1,row2, row3, row4])

        # show the camera to the user
        cv2.imshow("Vision Stack", frame_vision_stack)




if __name__ == "__main__":
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y)}
    )
    picam2.configure(config)
    picam2.start()


    # use default match settings
    one_v_one_match(match_settings, picam2)