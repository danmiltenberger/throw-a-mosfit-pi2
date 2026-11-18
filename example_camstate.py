from tam_classes import CameraState, BotCommand
from tam_frame import load_image_as_frame, show_frame
from tam_vision import get_camerastate
from tam_hsv import load_search_dict_from_csv
from tam_decide import get_botcom_from_cam
from tam_draw import draw_camerastate_to_cam, add_text_top

# load frames
left_frame = load_image_as_frame("hsv_photos/all_in_one_left.png")
right_frame = load_image_as_frame("hsv_photos/all_in_one_right.png")

# load the usual suspects
search_dict = load_search_dict_from_csv()

# get the camstates
cs_left = get_camerastate(left_frame, search_dict)
cs_right = get_camerastate(right_frame, search_dict, is_left=False)

bot_command = get_botcom_from_cam(cs_left)
left_frame = draw_camerastate_to_cam(left_frame, cs_left, our_left_is_green= False)
left_frame = draw_camerastate_to_cam(left_frame, cs_right, our_left_is_green= False)



# write bot decisions to the frame
left_frame = add_text_top(left_frame, str(bot_command))

show_frame(left_frame)