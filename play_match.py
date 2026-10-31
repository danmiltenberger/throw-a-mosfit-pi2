import time
from classes import BotCommand, DetectedObject
from menu_constants import get_button_status, BUTTON_STATUS, get_status_str, end, OUR_LEFT_GOAL, OUR_TEAM_COLOR
from I2C_write import write_lcd_lines
from tam_library_analyze_camera import get_detected_object
import cv2
from constants import BALL_RED

def one_v_one_match(match_settings: dict):


    ball_status = "???"
    hat_y_status = "???"
    hat_b_status = "???"
    bot_command = BotCommand()


    cap = cv2.VideoCapture(0)
 


 


    time_start = time.perf_counter()
    while True:

        # check if the program should quit
        button_status = get_button_status()
        match_settings[BUTTON_STATUS] = get_status_str(button_status)
        if button_status[end]:
            return

        # get each frame
        _, frame = cap.read()

        cv2.imshow("camera", frame)

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

