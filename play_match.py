import time
from classes import BotCommand, DetectedObject
from menu_constants import get_button_status, BUTTON_STATUS, get_status_str, end, OUR_LEFT_GOAL, OUR_TEAM_COLOR, match_settings
from I2C_write import write_lcd_lines
from tam_library_analyze_camera import get_detected_object
import cv2
from constants import BALL_RED
from bot_vision import get_frame
from picamera2 import Picamera2 #type: ignore
from constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y


def one_v_one_match(match_settings: dict, picam2):


    ball_status = "???"
    hat_y_status = "???"
    hat_b_status = "???"
    bot_command = BotCommand()

    time_start = time.perf_counter()
    while True:

        # check if the program should quit
        button_status = get_button_status()
        match_settings[BUTTON_STATUS] = get_status_str(button_status)
        if button_status[end]:
            return

        # get each frame
        frame = get_frame(picam2)
        frame_og = frame.copy()

        # Convert BGR to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)



        # search the frame for the ball
        detected = get_detected_object(BALL_RED, hsv)

        if detected is None:
            ball_status = "???" 
        else:
            ball_status = str(round(detected.distance_from_bot,1))


        # print information to the LCD
        time_current = time.perf_counter()
        time_elapsed = str(round(time_current - time_start,2))
        row1 = f"Match! {time_elapsed} US: {match_settings[OUR_TEAM_COLOR]}, L: {match_settings[OUR_LEFT_GOAL]}"
        row2 = f"bal {ball_status}, hat_y {hat_y_status} hat_b {hat_b_status}"
        row3 = f"com: {bot_command}"
        row4 = match_settings[BUTTON_STATUS]
        write_lcd_lines([row1,row2, row3, row4])

        # show the camera to the user
        cv2.imshow("camera", frame_og)
        if cv2.waitKey(1) & 0xFF == ord("q"):
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