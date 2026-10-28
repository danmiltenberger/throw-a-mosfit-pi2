from tam_library import show_frame
from tam_library_analyze_camera import get_detected_object,load_image_as_frame
from tam_library_draw_field import (
    draw_field_from_field_state, 
    get_field_frame, 
    draw_left_aligned_text, 
    inches_to_screen,
    convert_to_px,
)

from tam_library_front_and_top_down import convert_to_field
from classes import FieldState, DetectedObject
from constants_points import *
import cv2
from constants import *
import numpy as np
import math


def test_get_fieldstate_from_frame():

    print("testing get_fieldstate_from_frame")

    image_name : str = "6ft_center_blue"
    image_path = "training_data/" + image_name + ".png"

    frame_camera = load_image_as_frame(image_path)
    hsv_frame = cv2.cvtColor(frame_camera, cv2.COLOR_BGR2HSV)

    frame_field = get_field_frame()


    obj_str = HAT_BLUE
    obj_draw_color = search_dict[obj_str][DRAW_COLOR]


    field_state = FieldState(
        our_bot_pos_in= FIELD_GOALBOX_CENTER_BOTTOM
    )

    detected_obj = get_detected_object(
        field_state= field_state,
        hsv_frame= hsv_frame,
        object_name= obj_str
    )

    if detected_obj is not None:
        frame_camera = annotate_frame_with_obj(frame_camera, detected_obj, obj_str)

        obj_field_pos_in = convert_to_field(
            robot_pos=field_state.our_bot_pos_in,
            robot_bearing_rad= field_state.our_bot_bearing_rad,
            object_bearing_rad= detected_obj.bearing_rad,
            object_dis= detected_obj.distance_from_bot
        )

        obj_field_pos_px = inches_to_screen(obj_field_pos_in)

        obj_field_pos_px_cv2 = (int(obj_field_pos_px.x), int(obj_field_pos_px.y))

        frame_field = cv2.circle(
            center= obj_field_pos_px_cv2,
            color= obj_draw_color,
            img= frame_field,
            radius= convert_to_px(HAT_DIAM_IN/2),
            thickness= 5
        )

        show_frame(frame_camera, image_name)
        show_frame(frame_field, "field")
    else:
        print("detected no objects")


def annotate_frame_with_obj(frame: np.ndarray, obj: DetectedObject, object_name: str, write_text: bool = True) -> np.ndarray:


    draw_color = search_dict[object_name][DRAW_COLOR]

    # draw a bounding square
    left = int(obj.center_pos_on_screen_px.x - obj.width_px /2)
    top = int(obj.center_pos_on_screen_px.y - obj.width_px /2)

    frame = cv2.rectangle(
        color= draw_color,
        img= frame,
        pt1= (left, top),
        pt2= (left + obj.width_px, top + obj.width_px)
    )

    # write values to the right of the square
    if write_text:
        print_list = [
        object_name,
        f"{round(obj.distance_from_bot,1)}in",
        f"{round(math.degrees(obj.bearing_rad,),1)}deg",
        f"{obj.width_px} px"
        ]

        frame = draw_left_aligned_text(
            center_point= obj.center_pos_on_screen_px,
            color= BLACK,
            image= frame,
            lines= print_list,
            x_offset= int(obj.width_px /2) + 5
        )

    return frame


def search_and_annotate(frame_camera: np.ndarray, search_obj: str,field_state:FieldState) -> np.ndarray:
    '''from the camera frame, look for the given object like BALL_RED
    and annotate the frame by drawing a bounding shape'''

    hsv_frame = cv2.cvtColor(frame_camera.copy(), cv2.COLOR_BGR2HSV)

    
    detected_obj= get_detected_object(
        field_state= field_state,
        object_name= search_obj,
        hsv_frame=hsv_frame
    )


    if detected_obj is None:
        return frame_camera

    camera_frame_annotated = annotate_frame_with_obj(
        write_text= False,
        object_name= search_obj,
        frame= frame_camera,
        obj= detected_obj,
    )

    return camera_frame_annotated




if __name__ == "__main__":
    test_get_fieldstate_from_frame()

    