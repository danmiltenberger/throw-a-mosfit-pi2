from tam_frame import overlap_frames, show_frame_in_loop
from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_hsv import load_search_dict_from_csv
from tam_vision import get_camerastate
from tam_draw import draw_camerastate_to_cam


# one time setup

# cameras
camL, camR = setup_left_right_cams()

# values to look for
search_dict = load_search_dict_from_csv()



# bools (change this later with switches)
our_team_is_yellow : bool = True
our_goal_is_green_purple : bool = False

overlap = int(input("enter overlap percentage as an int ie 80: "))

while True:
    frame_l, frame_r = get_left_right_frames(camL, camR)

    cs_left = get_camerastate(frame_l, search_dict)
    cs_right = get_camerastate(frame_r, search_dict)

    frame_l = draw_camerastate_to_cam(frame_l, cs_left)
    frame_r = draw_camerastate_to_cam(frame_r, cs_right)

    combined = overlap_frames(frame_l, frame_r, overlap)

    if show_frame_in_loop(combined) == False:
        break