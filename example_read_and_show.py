from tam_binocular import get_left_right_frames, setup_left_right_cams
from tam_frame import concat_frames, show_frame_in_loop
from tam_vision import get_camerastate
from tam_draw import draw_camerastate_to_cam
from tam_hsv import load_search_dict_from_csv
from tam_decide import get_botcom_from_cam
from run_ard_manually import connect, send_bot_com
from picamera2 import Picamera2


def example_read_and_show():

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

        # get camera states
        cs_left = get_camerastate(
            frame_camera= frame_l,
            is_left= True,
            our_team_is_yellow= our_team_is_yellow,
            search_dict= search_dict
        )

        cs_right = get_camerastate(
            frame_camera= frame_r,
            is_left= False,
            our_team_is_yellow= our_team_is_yellow,
            search_dict= search_dict
        )

        # annotate and show
        frame_l_anno = draw_camerastate_to_cam(
            cs= cs_left,
            frame_cam= frame_l,
            our_left_is_green= our_goal_is_green_purple,
            our_team_is_yellow= our_team_is_yellow,
        )

        frame_r_anno = draw_camerastate_to_cam(
            cs= cs_right,
            frame_cam= frame_r,
            our_left_is_green= our_goal_is_green_purple,
            our_team_is_yellow= our_team_is_yellow,
        )

        # get decisions
        botcom = get_botcom_from_cam(cs_left,)

        send_bot_com(ser, botcom)

        combined = concat_frames(frame_l_anno, frame_r_anno, "DOWN")

        if show_frame_in_loop(combined) == False:
            break


if __name__ == "__main__":
    example_read_and_show()