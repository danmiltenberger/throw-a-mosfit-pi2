from tam_binocular import get_left_right_frames, setup_left_right_cams
from tam_frame import concat_frames, show_frame
from tam_vision import get_camerastate
from tam_draw import draw_camerastate_to_cam
from tam_hsv import load_search_dict_from_csv
from tam_decide import get_botcom_from_cam
from tam_constants import SCREEN_CENTER_X
from tam_topdown import calc_angle_from_screen_center
from tam_arduino import send_bot_command, connect
from tam_commands import BotCommand, BOT_ROTATE_LEFT, BOT_ROTATE_RIGHT, BOT_FORWARD
from picamera2 import Picamera2
import time
import math
import serial


def example_search_for_ball():

    # one time setup

    # cameras
    camL, camR = setup_left_right_cams()

    # values to look for
    search_dict = load_search_dict_from_csv()

    # serial
    ser = connect("/dev/ttyACM0")

    # bools (change this later with switches)
    our_team_is_yellow : bool = True
    our_goal_is_green_purple : bool = False

    while True:
        frame_l, frame_r = get_left_right_frames(camL, camR)

        cs_left = get_camerastate(frame_l, search_dict, is_left=True)
        frame_l_anno = draw_camerastate_to_cam(frame_cam=frame_l, cs= cs_left)

        #show_frame(frame_l_anno)
        duration = 0.1

        # if it's not in the frame, rotate until you see it
        if cs_left.ball_in_frame == False:
            
            slow_rotate_and_look = BotCommand(BOT_ROTATE_LEFT, dur_sec=10, speed_percent= 30)

            send_bot_command(ser, slow_rotate_and_look)

        else:
            # try and center the ball in the frame

            angle_from_bot = calc_angle_from_screen_center(cs_left.ball_pos_px)
            deg_from_bot = math.degrees(angle_from_bot)

            if deg_from_bot < -5:
                #input("centering ball: hit enter to rotate left")
                careful_left = BotCommand(BOT_ROTATE_LEFT, dur_sec=1, speed_percent= 30)
                send_bot_command(ser, careful_left)

            elif deg_from_bot > 5:

                careful_right = BotCommand(BOT_ROTATE_RIGHT, dur_sec=1, speed_percent= 30)
                send_bot_command(ser, careful_right)

            # drive to the ball!
            else:
                input("drive to ball?")
                move_closer = BotCommand(BOT_FORWARD, dur_sec=1, speed_percent= 30)
                send_bot_command(ser, move_closer)



if __name__ == "__main__":
    example_search_for_ball()