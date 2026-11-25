from tam_frame import show_frame_in_loop, overlap_frames
from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_vision import get_dual_camerastate
from tam_hsv import load_search_dict_from_csv
from tam_classes import get_settings
from tam_draw import draw_dualcamerastate_to_cam


camL, camR = setup_left_right_cams()
search_dict = load_search_dict_from_csv()
match_set = get_settings(our_team_is_orange= False)

while True:
    frame_left, frame_right = get_left_right_frames(camL,camR)

    dual_cs = get_dual_camerastate(frame_left=frame_left, frame_right=frame_right, search_dict=search_dict, match_set=match_set)
    frame_with_cs = draw_dualcamerastate_to_cam(dual=dual_cs, left_frame=frame_left, right_frame=frame_right,settings= match_set)


    if show_frame_in_loop(frame_with_cs) == False:
        break








