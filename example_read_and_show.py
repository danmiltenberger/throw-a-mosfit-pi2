from tam_binocular import get_left_right_frames, setup_left_right_cams
from tam_frame import concat_frames, show_frame_in_loop
from tam_vision import get_camerastate
from tam_draw import draw_camerastate_to_cam
from tam_hsv import load_search_dict_from_csv
from picamera2 import Picamera2


def example_read_and_show():
    camL, camR = setup_left_right_cams()
    search_dict = load_search_dict_from_csv()


    while True:
        frame_l, frame_r = get_left_right_frames(camL, camR)

        cs_left = get_camerastate(
            frame_camera= frame_l,
            is_left= True,
            our_team_is_yellow= True,
            search_dict= search_dict
        )

        cs_right = get_camerastate(
            frame_camera= frame_r,
            is_left= False,
            our_team_is_yellow= True,
            search_dict= search_dict
        )

        frame_l_anno = draw_camerastate_to_cam(
            cs= cs_left,
            frame_cam= frame_l,
            our_left_is_green= False,
            our_team_is_yellow= True,
        )

        frame_r_anno = draw_camerastate_to_cam(
            cs= cs_right,
            frame_cam= frame_r,
            our_left_is_green= False,
            our_team_is_yellow= True,
        )

        combined = concat_frames(frame_l_anno, frame_r_anno, "DOWN")

        if show_frame_in_loop(combined) == False:
            break


if __name__ == "__main__":
    example_read_and_show()