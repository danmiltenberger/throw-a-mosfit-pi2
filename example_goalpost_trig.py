from tam_frame import get_field_frame, show_frame, load_image_as_frame, concat_frames, resize_frame
from tam_topdown import calc_pos_and_angle_from_goalposts, calc_angle_from_screen_center
from tam_vision import get_camerastate
from tam_hsv import load_search_dict_from_csv
from tam_points import FIELD_GOALBOX_CENTER_BOTTOM, GOALPOST_NORTHEAST, GOALPOST_NORTHWEST
from tam_constants import BEARING_NORTH
from tam_draw import draw_robot_to_field, draw_arrow_point_to_point, draw_camerastate_to_cam, add_text_top, draw_angle_lines_on_camera_frame
from tam_colors import GREEN, FUCHSIA
import math
from tam_classes import Point




frame_field = get_field_frame(left_is_green=True)

frame_left = load_image_as_frame("hsv_photos/all_in_one_left.png")
frame_right = load_image_as_frame("hsv_photos/all_in_one_right.png")
search_dict = load_search_dict_from_csv()

cs_left = get_camerastate(frame_left, search_dict)
cs_right = get_camerastate(frame_right, search_dict)

# east is green
rad_LE = calc_angle_from_screen_center(cs_left.gpgr_pos_px)
rad_LW = calc_angle_from_screen_center(cs_left.gppr_pos_px)

rad_RE = calc_angle_from_screen_center(cs_right.gpgr_pos_px)
rad_RW = calc_angle_from_screen_center(cs_right.gppr_pos_px)


rad_dict = {
    "LE" : rad_LE,  
    "LW" : rad_LW,  
    "RE" : rad_RE,  
    "RW" : rad_RW  
}

bot_pos_default = FIELD_GOALBOX_CENTER_BOTTOM
bot_rad_default = BEARING_NORTH

point_L_default = Point(
    x= FIELD_GOALBOX_CENTER_BOTTOM.x - 2.5,
    y= FIELD_GOALBOX_CENTER_BOTTOM.y
)

point_R_default = Point(
    x= FIELD_GOALBOX_CENTER_BOTTOM.x + 2.5,
    y= FIELD_GOALBOX_CENTER_BOTTOM.y
)

# bot_pos, bot_rad = calc_pos_and_angle_from_goalposts(
#     rad_LE= rad_LE,
#     rad_LW= rad_LW,
#     rad_RW= rad_RW,
#     rad_RE = rad_RE,
#     rad_BOT= bot_rad_default,
#     pos_BOT= bot_pos_default
# )

# for key in rad_dict.keys():
#     print(key, round(math.degrees(rad_dict[key])), "deg")

# print(bot_pos, bot_rad)

frame_field = draw_robot_to_field(
    frame_field, bot_pos_default, bot_rad_default
)

# draw the lines
frame_field = draw_arrow_point_to_point(frame_field, point_L_default, GOALPOST_NORTHWEST, color= GREEN, is_in_inches=True, label_lines=["LW"])
frame_field = draw_arrow_point_to_point(frame_field, point_L_default, GOALPOST_NORTHEAST, color= FUCHSIA, is_in_inches=True, label_lines=["LE"])
frame_field = draw_arrow_point_to_point(frame_field, point_R_default, GOALPOST_NORTHWEST, color= GREEN, is_in_inches=True, label_lines=["RW"])
frame_field = draw_arrow_point_to_point(frame_field, point_R_default, GOALPOST_NORTHEAST, color= FUCHSIA, is_in_inches=True, label_lines=["RE"])


# show both detections to the same frame for a cool overlay effect

frame_left_overlay = draw_angle_lines_on_camera_frame(frame_left, list_of_angles_deg=[-20, -15, -10, -5, 0, 5, 10, 15, 20], add_text=True)
frame_left_overlay = draw_camerastate_to_cam(frame_left_overlay, cs_left)
frame_left_overlay = draw_camerastate_to_cam(frame_left_overlay, cs_right)
frame_left_overlay = add_text_top(frame_left_overlay, "Left Camera with both overlays")



show_frame(frame_left_overlay)

# frame_left_annotated = draw_camerastate_to_cam(frame_left, cs_left)
# frame_left_annotated = add_text_top(frame_left_annotated, "LEFT")

# frame_right_annotated = draw_camerastate_to_cam(frame_right, cs_right)
# frame_right_annotated = add_text_top(frame_right_annotated, "RIGHT")

# left_frames = concat_frames(frame_left_annotated, frame_right_annotated, "DOWN")
# screen = concat_frames(left_frames, frame_field)
# screen = resize_frame(screen, 0.5)
# show_frame(screen)

