from tam_classes import CameraState
from tam_frame import load_image_as_frame, show_frame, overlap_frames
from tam_hsv import load_search_dict_from_csv
from tam_draw import draw_camerastate_to_cam
from tam_vision import get_camerastate
from tam_triangulate import triangulate_object_wrt_bot


# load frames
left_frame = load_image_as_frame("hsv_photos/all_in_one_left.png")
right_frame = load_image_as_frame("hsv_photos/all_in_one_right.png")

# load the usual suspects
search_dict = load_search_dict_from_csv()

# bools
our_left_is_green = False
our_team_is_yellow = False

cs_left = get_camerastate(
    our_left_is_green=our_left_is_green,
    is_left=True,
    frame_camera= left_frame,
    search_dict= search_dict,
)

cs_right = get_camerastate(
    our_left_is_green=our_left_is_green,
    is_left=False,
    frame_camera= right_frame,
    search_dict= search_dict,
)


left_frame = draw_camerastate_to_cam(left_frame, cs_left)
right_frame = draw_camerastate_to_cam(right_frame, cs_right)

triangulate_object_wrt_bot(cs_left.ball_pos_px, cs_right.ball_pos_px)

overlapped = overlap_frames(left_frame, right_frame)

show_frame(overlapped)