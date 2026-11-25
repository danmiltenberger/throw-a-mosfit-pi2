from tam_classes import CameraState, FieldState, Settings, get_settings
from tam_frame import (
    load_image_as_frame,
    show_frame,
    get_field_frame,
    get_dashboard,
    concat_frames

)
from tam_hsv import load_search_dict_from_csv
from tam_draw import (
    draw_camerastate_to_cam,
    draw_fieldstate,
    draw_dualcamerastate_to_cam
)

from tam_vision import get_camerastate, get_fieldstate, get_dual_camerastate
from tam_decide import get_init_fieldstate
from tam_constants import BEARING_NORTH
from tam_points import FIELD_GOALBOX_CENTER_BOTTOM
from tam_goalpost import PoseTracker, build_total_goalpost, get_bot_pose_from_goalposts

# load frames
left_frame = load_image_as_frame("hsv_photos/all_in_one_left.png")
right_frame = load_image_as_frame("hsv_photos/all_in_one_right.png")

# load the usual suspects
search_dict = load_search_dict_from_csv()
match_set = get_settings(our_team_is_orange= False)
field_frame = get_field_frame(match_set=match_set)


match_set.draw_ball = False

prev_fs = get_init_fieldstate()


# camera 
dual = get_dual_camerastate(match_set=match_set, frame_left= left_frame, frame_right=right_frame, search_dict=search_dict)

blended = draw_dualcamerastate_to_cam(dual, match_set, left_frame=left_frame)


dashboard = concat_frames(blended, field_frame)
show_frame(dashboard)

