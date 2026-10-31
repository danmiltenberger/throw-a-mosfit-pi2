import time
from classes import BotCommand, DetectedObject
from menu_constants import get_button_status, BUTTON_STATUS, get_status_str, end, OUR_LEFT_GOAL, OUR_TEAM_COLOR, match_settings
from I2C_write import write_lcd_lines
from tam_library_analyze_camera import get_detected_object
from tam_library_draw_field import get_field_frame
from tam_library import save_frame_as_png, show_frame_in_loop
import cv2
from constants import BALL_RED
from bot_vision import get_frame, vision_full_stack
from picamera2 import Picamera2 #type: ignore
from constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y


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
        match_settings[BUTTON_STATUS] = get_status_str(button_status)
        if button_status[end]:

            if save_frame_on_exit:
                save_frame_as_png(frame_og)
            return

        frame_vision_stack = vision_full_stack(frame, frame_field=field_frame)

        # print information to the LCD
        time_current = time.perf_counter()
        time_elapsed = str(round(time_current - time_start,2))
        row1 = f"Match! {time_elapsed} US: {match_settings[OUR_TEAM_COLOR]}, L: {match_settings[OUR_LEFT_GOAL]}"
        row2 = f"bal {ball_status}, hat_y {hat_y_status} hat_b {hat_b_status}"
        row3 = f"com: {str(bot_command)}"
        row4 = match_settings[BUTTON_STATUS]
        write_lcd_lines([row1,row2, row3, row4])

        # show the camera to the user
        if not show_frame_in_loop(frame_vision_stack, window_name="Frame", delay_ms=1):
            break




if __name__ == "__main__":
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y)}
    )
    picam2.configure(config)
    picam2.start()


    # use default match settings
    one_v_one_match(match_settings, picam2)