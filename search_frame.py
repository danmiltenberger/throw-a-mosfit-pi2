from constants import *
import cv2
import numpy as np
from classes import FieldState, DetectedObject, Point
from typing import Sequence
from variables import *
from constants import *
from tam_library import append_dict_to_csv
from convert_from_front_to_top_down import calc_distance_from_bot, calc_angle_from_screen_center

search_dict = {
    BALL_RED: {
        DRAW_COLOR: RED,
        HSV_LO: np.array([0, 200, 0], dtype=np.uint8),
        HSV_HI: np.array([10, 255, 157], dtype=np.uint8),
        KNOWN_WIDTH: BALL_RED_DIAM,
        ANALYSIS_SHAPE : CIRC,
    },
    BALL_YELLOW: {
        DRAW_COLOR: YELLOW,
        HSV_LO: [21, 103, 170],
        HSV_HI: [35, 201, 250],
        KNOWN_WIDTH: BALL_YELLOW,
        ANALYSIS_SHAPE : CIRC,
    },
    HAT_BLUE: {
        DRAW_COLOR: BLUE,
        HSV_LO: [90, 163, 125],
        HSV_HI: [110, 255, 205],
        KNOWN_WIDTH: HAT_DIAM,
        ANALYSIS_SHAPE : RECT,
    },
    HAT_YELLOW: {
        DRAW_COLOR: YELLOW,
        HSV_LO: [22, 150, 174],
        HSV_HI: [42, 210, 228],
        KNOWN_WIDTH: HAT_DIAM,
        ANALYSIS_SHAPE : RECT,
    },
    HAT_FUCHSIA: {
        DRAW_COLOR: FUCHSIA,
        HSV_LO: "to_be_determined",
        HSV_HI: "to_be_determined",
        KNOWN_WIDTH: HAT_DIAM,
        ANALYSIS_SHAPE : RECT,
    },
    HAT_GREEN: {
        DRAW_COLOR: GREEN,
        HSV_LO: "to_be_determined",
        HSV_HI: "to_be_determined",
        KNOWN_WIDTH: HAT_DIAM,
        ANALYSIS_SHAPE : RECT,
    },
}


def get_fieldstate_from_frame(frame: np.ndarray, timestep: float = 0, append_to_dict: bool = False, csv_path: str = "") -> FieldState:
    '''search the frame for each object and return a fieldstate'''

    def get_contours(hsv_hi, hsv_lo) -> Sequence[np.ndarray]:

        # create a mask using the hsv values
        mask = cv2.inRange(hsv, hsv_hi, hsv_lo)

        # get the contours from the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def get_detected_object(object_name: str) -> DetectedObject | None:
        contours : Sequence[np.ndarray] = get_contours(hsv_hi=search_dict[object_name][HSV_HI], hsv_lo=search_dict[object_name][HSV_LO])
        best_contour, best_area = get_best_contour(contours)

        # if there is no contour, this object has not been detected, go to next object
        if best_contour is None:
            this_frame_field_state.found_dict[object_name] = False
            return None
        else:
            this_frame_field_state.found_dict[object_name] = True

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

    this_frame_field_state = FieldState()

    # convert to hsv for processing
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if search_for_ball_red:
        ball_object = get_detected_object(BALL_RED)
        if ball_object is not None:
            this_frame_field_state.ball_pos_in = ball_object.pos_wrt_bot

    if search_for_ball_yellow:
        ball_object = get_detected_object(BALL_YELLOW)
        if ball_object is not None:
            pass    # TODO

    if search_for_hat_blue:
        hat_object = get_detected_object(HAT_BLUE)
        if hat_object is not None:
            pass # TODO


    if append_to_dict:
        append_dict_to_csv(csv_file_path=csv_path, data= this_frame_field_state.to_dict())

    return this_frame_field_state


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


        
