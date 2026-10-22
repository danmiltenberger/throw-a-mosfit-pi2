from constants import *
import cv2
import numpy as np
from classes import FieldState, DetectedObject, Point
from typing import Sequence
from variables import *
from constants import *
from tam_library import append_dict_to_csv, load_image_as_frame, show_frame, debugprint
from convert_from_front_to_top_down import calc_distance_from_bot, calc_angle_from_screen_center


def get_fieldstate_from_frame(frame: np.ndarray, timestep: float = 0, append_to_dict: bool = False, csv_path: str = "") -> FieldState:
    '''search the frame for each object and return a fieldstate'''



    this_frame_field_state = FieldState()

    # convert to hsv for processing
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if search_for_ball_red:
        ball_object = get_detected_object(object_name=BALL_RED, field_state= this_frame_field_state, hsv_frame= hsv)
        if ball_object is not None:
            this_frame_field_state.ball_pos_in = ball_object.pos_wrt_bot

    if search_for_ball_yellow:
        ball_object = get_detected_object(object_name=BALL_YELLOW, hsv_frame=hsv, field_state=this_frame_field_state)
        if ball_object is not None:
            pass    # TODO

    # if search_for_hat_blue:
    #     hat_object = get_detected_object(HAT_BLUE)
    #     if hat_object is not None:
    #         pass # TODO


    if append_to_dict:
        append_dict_to_csv(csv_file_path=csv_path, data= this_frame_field_state.to_dict())

    return this_frame_field_state


def get_contours(hsv, hsv_hi, hsv_lo) -> Sequence[np.ndarray]:

    # create a mask using the hsv values
    print("hsv_hi: ", hsv_hi, "hsv_lo:", hsv_lo)
    mask = cv2.inRange(hsv, hsv_hi, hsv_lo)

    show_frame(mask, "mask")

    # get the contours from the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def get_detected_object(field_state: FieldState, object_name: str, hsv_frame) -> DetectedObject | None:
    contours : Sequence[np.ndarray] = get_contours(hsv_frame, hsv_hi=search_dict[object_name][HSV_HI], hsv_lo=search_dict[object_name][HSV_LO])
    best_contour, best_area = get_best_contour(contours)

    # if there is no contour, this object has not been detected, go to next object
    if best_contour is None:
        field_state.found_dict[object_name] = False
        return None
    else:
        field_state.found_dict[object_name] = True

    this_detect = DetectedObject()

    if search_dict[object_name][ANALYSIS_SHAPE] == CIRC:
        (x, y), radius = cv2.minEnclosingCircle(best_contour)
        this_detect.center_pos_on_screen_px = Point(x,y)
        this_detect.width_px = int(radius * 2)
        this_detect.area_px = int(np.pi * radius * radius)

    elif search_dict[object_name][ANALYSIS_SHAPE] == RECT:
        left_x, top_y, width, height = cv2.boundingRect(best_contour)
        x_center = int(left_x + width / 2)
        y_center = int(top_y + height / 2)

        this_detect.center_pos_on_screen_px = Point(x_center,y_center)
        this_detect.width_px = width
        this_detect.area_px = width * height

    else:
        print("couldn't find analysis shape, expected RECT or CIRC")

    # convert to top down
    this_detect.distance_from_bot = calc_distance_from_bot(known_width_in= search_dict[object_name][KNOWN_WIDTH], percieved_width_px= this_detect.width_px)
    this_detect.bearing_rad = calc_angle_from_screen_center(this_detect.center_pos_on_screen_px)

    this_detect.get_pos_wrt_bot()

    return this_detect


def get_best_contour(contours):

    check_min_area: bool = False
    check_min_circularity: bool = False
    min_area: int = 0
    min_circularity: int = 0

    best_contour = None
    best_area = -1.0

    for contour in contours:
        area = cv2.contourArea(contour)

        if check_min_area:
            if area < min_area:
                continue

        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue

        if check_min_circularity:
            circularity = 4.0 * np.pi * area / perimeter**2
            if circularity < min_circularity:
                continue

        if area > best_area:
            best_area = area
            best_contour = contour

    return best_contour, best_area


        
if __name__ == "__main__":

    cam_frame = load_image_as_frame("training_data/vlcsnap-2026-10-05-16h43m03s033.png")

    # convert to hsv for processing
    hsv = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2HSV)
    show_frame(hsv)

    field_state = FieldState()
    

    obj = get_detected_object(field_state=field_state, hsv_frame=hsv, object_name=BALL_RED)

    field_state = get_fieldstate_from_frame(frame=cam_frame)

    print(field_state)
