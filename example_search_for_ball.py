from tam_binocular import get_left_right_frames, setup_left_right_cams
from tam_frame import concat_frames, show_frame_in_loop
from tam_vision import get_camerastate
from tam_draw import draw_camerastate_to_cam
from tam_hsv import load_search_dict_from_csv
from tam_decide import get_botcom_from_cam
from run_ard_manually import connect, send_command
from picamera2 import Picamera2
import time


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

        if cs_left.ball_in_frame == False:
            print("turning left to look for ball")
            duration = 0.1
            send_command(ser, "q", duration= duration)

            time.sleep(duration)

if __name__ == "__main__":
    example_search_for_ball()