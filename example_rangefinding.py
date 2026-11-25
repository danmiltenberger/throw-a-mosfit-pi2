from tam_frame import show_frame_in_loop, overlap_frames, flip_rightside_up
from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_vision import get_dual_camerastate
from tam_hsv import load_search_dict_from_csv
from tam_classes import get_settings
from tam_draw import draw_dualcamerastate_to_cam, add_text_left_of_point, get_midpoint
import numpy as np
import cv2
import math
from tam_topdown import calc_range

camL, camR = setup_left_right_cams()
search_dict = load_search_dict_from_csv()
match_set = get_settings(our_team_is_orange= False)

while True:

    frame_left, frame_right = get_left_right_frames(camL,camR)

    # this is just for testing, I accidentally mounted the cameras upside down
    frame_right_fixed = flip_rightside_up(frame_left.copy())
    frame_left_fixed = flip_rightside_up(frame_right.copy())

    dual_cs = get_dual_camerastate(frame_left=frame_left_fixed, frame_right=frame_right_fixed, search_dict=search_dict, match_set=match_set)
    frame_with_cs = draw_dualcamerastate_to_cam(dual=dual_cs, left_frame=frame_left_fixed, right_frame=frame_right_fixed,settings= match_set)

    dis_in, bear_rad = calc_range(dual_cs.left.ball_pos_px, dual_cs.right.ball_pos_px)
    dis_in = round(dis_in,2)
    bear_deg = round(math.degrees(bear_rad))

    mid_sighting = get_midpoint(dual_cs.left.ball_pos_px, dual_cs.right.ball_pos_px)
    frame_with_cs = add_text_left_of_point(center_left=mid_sighting, lines=[str(dis_in)+"in", str(bear_deg)+"deg"], frame=frame_with_cs)


    if show_frame_in_loop(frame_with_cs) == False:
        break










