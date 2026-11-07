## all the functions that convert the camera frame into bools, floats, etc

import cv2
import numpy as np
import math
from tam_classes import FieldState, Point, Detection
from tam_constants import (
    BALL_RED,
    HSV_HI,
    HSV_LO,
    WIDTH_PX,
    AREA_PX,
    CENTER_X_PX,
    CENTER_Y_PX,
    SHAPE,
    KNOWN_WIDTH,
    BEARING_NORTH,
    HAT_BLUE,
    HAT_YELLOW,
    OBJECT_NAME,
    HAT_FUCHSIA,
    HAT_GREEN,
    MIN_AREA_PX
)
from tam_points import FIELD_GOALBOX_CENTER_BOTTOM
from tam_colors import YELLOW, BLUE, RED, BLACK, PURPLE, GREEN
from tam_topdown import (
    calc_distance_from_bot,
    calc_angle_from_screen_center,
    convert_to_field,
)
from tam_draw import (
    add_text_top,
    draw_robot_to_field,
    draw_ball_to_field,
    draw_top_down_arrows,
    draw_object_to_frame,
)
from tam_frame import concat_frames
from typing import Sequence


def get_hsv_frame(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return hsv


def get_mask_frame(hsv_frame: np.ndarray, hsv_lo, hsv_hi) -> np.ndarray:
    mask = cv2.inRange(hsv_frame, lowerb=hsv_lo, upperb=hsv_hi)

    return mask


def get_contours(frame_mask: np.ndarray) -> Sequence:
    """Find external contours in a binary/grayscale mask.

    Returns:
        tuple: (contours, hierarchy)
    """
    if not isinstance(frame_mask, np.ndarray):
        raise TypeError(
            f"frame_mask must be numpy.ndarray, got {type(frame_mask).__name__}"
        )

    if frame_mask.ndim != 2:
        raise ValueError(
            f"frame_mask must be a 2D grayscale mask, got shape {frame_mask.shape}"
        )

    if frame_mask.size == 0:
        raise ValueError("frame_mask must not be empty")

    contours, hierarchy = cv2.findContours(
        frame_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    return contours


def get_object_info_from_contours(
    contours, analyze_as_circle: bool = True, object_name: str = "NO_NAME"
) -> dict:
    """
    Analyze contours as circles or squares.

    Returns a dictionary containing object measurements in pixel units:
        - WIDTH_PX: diameter for circles, bounding-box width for squares
        - AREA_PX: contour area in pixels
        - CENTER_X_PX: horizontal center position
        - CENTER_Y_PX: vertical center position
        - SHAPE: CIRCLE or SQUARE

    If multiple contours are supplied, their measurements are combined into
    one bounding region and total area.
    """

    if contours is None:
        raise TypeError("contours must not be None")

    if not isinstance(contours, (list, tuple, np.ndarray)):
        raise TypeError(
            f"contours must be a list, tuple, or ndarray, "
            f"got {type(contours).__name__}"
        )

    if not isinstance(analyze_as_circle, bool):
        raise TypeError(
            f"analyze_as_circle must be a bool, got {type(analyze_as_circle).__name__}"
        )

    if len(contours) == 0:
        return {
            WIDTH_PX: 0.0,
            AREA_PX: 0.0,
            CENTER_X_PX: 0.0,
            CENTER_Y_PX: 0.0,
            SHAPE: "NO_SHAPE",
        }

    total_area = 0.0
    x_min = y_min = np.inf
    x_max = y_max = -np.inf

    for contour in contours:
        if not isinstance(contour, np.ndarray):
            raise TypeError("each contour must be a numpy.ndarray")

        if contour.ndim != 3 or contour.shape[1] != 1 or contour.shape[2] != 2:
            raise ValueError(
                "each contour must have shape (N, 1, 2), " f"got {contour.shape}"
            )

        area = cv2.contourArea(contour)
        total_area += area

        x, y, w, h = cv2.boundingRect(contour)
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x + w)
        y_max = max(y_max, y + h)

    combined_width = x_max - x_min
    combined_height = y_max - y_min
    center_x = x_min + combined_width / 2
    center_y = y_min + combined_height / 2

    if analyze_as_circle:
        # Diameter of a circle with the same area as the detected object(s)
        width = 2.0 * np.sqrt(total_area / np.pi)
        shape = "CIRCLE"
    else:
        # Use the combined bounding box width for a square/rectangular object
        width = float(combined_width)
        shape = "SQUARE"

    return {
        WIDTH_PX: float(width),
        AREA_PX: float(total_area),
        CENTER_X_PX: float(center_x),
        CENTER_Y_PX: float(center_y),
        SHAPE: shape,
        OBJECT_NAME: object_name,
    }


def get_object_info_from_name(
    hsv_frame: np.ndarray, obj_name: str, search_dict: dict, analyze_as_circle: bool = True
) -> dict:
    hsv_lo = search_dict[obj_name][HSV_LO]
    hsv_hi = search_dict[obj_name][HSV_HI]

    mask_frame = get_mask_frame(hsv_frame=hsv_frame, hsv_hi=hsv_hi, hsv_lo=hsv_lo)

    contours = get_contours(mask_frame)

    # otherwise let's evaluate the contours
    object_info = get_object_info_from_contours(contours, analyze_as_circle)

    object_info[OBJECT_NAME] = OBJECT_NAME

    return object_info


def search_for_ball(
    hsv_frame: np.ndarray, fieldstate: FieldState, search_dict: dict
) -> FieldState:

    object_info = get_object_info_from_name(
        hsv_frame=hsv_frame, search_dict=search_dict, obj_name=BALL_RED
    )
    known_width_in = search_dict[BALL_RED][KNOWN_WIDTH]

    width_px = object_info[WIDTH_PX]
    screen_x = object_info[CENTER_X_PX]
    screen_y = object_info[CENTER_Y_PX]

    ball_distance_in = calc_distance_from_bot(known_width_in, width_px)

    screen_center = Point(screen_x, screen_y)
    ball_angle_rad = calc_angle_from_screen_center(screen_center)

    fieldstate.ball_pos_in = convert_to_field(
        object_bearing_rad=ball_angle_rad,
        object_dis=ball_distance_in,
        robot_bearing_rad=fieldstate.our_bot_bearing_rad,
        robot_pos=fieldstate.our_bot_pos_in,
    )

    return fieldstate


def search_for_bot(
    hsv_frame: np.ndarray, fieldstate: FieldState, search_dict: dict
) -> FieldState:

    if fieldstate.our_team_color == YELLOW:
        search_name = HAT_BLUE
    elif fieldstate.our_team_color == BLUE:
        search_name = HAT_YELLOW
    else:
        raise ValueError(
            f"Our team color is not YELLOW or BLUE, recieved {fieldstate.our_team_color}"
        )

    object_info = get_object_info_from_name(
        search_dict=search_dict, hsv_frame=hsv_frame, obj_name=search_name
    )

    known_width_in = search_dict[search_name][KNOWN_WIDTH]
    width_px = object_info[WIDTH_PX]
    screen_x = object_info[CENTER_X_PX]
    screen_y = object_info[CENTER_Y_PX]

    ball_distance_in = calc_distance_from_bot(known_width_in, width_px)

    screen_center = Point(screen_x, screen_y)
    ball_angle_rad = calc_angle_from_screen_center(screen_center)

    fieldstate.their_bot_pos_in = convert_to_field(
        object_bearing_rad=ball_angle_rad,
        object_dis=ball_distance_in,
        robot_bearing_rad=fieldstate.our_bot_bearing_rad,
        robot_pos=fieldstate.our_bot_pos_in,
    )

    return fieldstate


def get_fieldstate_from_frame(
    frame: np.ndarray, prev_fieldstate: FieldState | None, search_dict: dict
) -> FieldState:
    """Look through the frame and determine objects, positions, etc"""

    # some determinations require previous values. If not supplied, use defaults
    if prev_fieldstate is None:
        prev_fieldstate = FieldState()

    # start by assuming that nothing has changed, to be overwritten below
    new_fieldstate = prev_fieldstate

    hsv_frame = get_hsv_frame(frame)

    # search for ball
    new_fieldstate = search_for_ball(hsv_frame, new_fieldstate, search_dict)

    # search for bot
    new_fieldstate = search_for_bot(hsv_frame, new_fieldstate, search_dict)

    # search for goalposts

    return new_fieldstate


def get_annotated_frame(frame: np.ndarray, search_dict: dict) -> np.ndarray:

    annotated_frame = frame.copy()

    hsv_frame = get_hsv_frame(frame.copy())

    # search for ball
    ball_info = get_object_info_from_name(
        hsv_frame, search_dict=search_dict, obj_name=BALL_RED
    )
    annotated_frame = draw_object_to_frame(
        annotated_frame, color=RED, object_dict=ball_info
    )

    # search for goals
    goal_purple_info = get_object_info_from_name(hsv_frame, search_dict=search_dict, obj_name=HAT_FUCHSIA)
    goal_green_info = get_object_info_from_name(hsv_frame, search_dict=search_dict, obj_name=HAT_GREEN)

    annotated_frame = draw_object_to_frame(
        annotated_frame, goal_green_info, color= GREEN
    )

    annotated_frame = draw_object_to_frame(
        annotated_frame, goal_purple_info, color= PURPLE
    )

    return annotated_frame


def get_detection_from_name(obj_name: str, hsv_frame: np.ndarray, search_dict: dict) -> Detection:
    
    # load values to create the mask etc
    hsv_lo = search_dict[obj_name][HSV_LO]
    hsv_hi = search_dict[obj_name][HSV_HI]
    known_width_in = search_dict[obj_name][KNOWN_WIDTH]
    min_area_px = int(search_dict[obj_name][MIN_AREA_PX])

    # create the thing to be returned
    detection = Detection()
    detection.name = obj_name
    detection.in_frame = False

    mask_frame = get_mask_frame(hsv_frame=hsv_frame, hsv_hi=hsv_hi, hsv_lo=hsv_lo)
    contours = get_contours(mask_frame)

    if contours is None:
        raise TypeError("contours must not be None")

    if not isinstance(contours, (list, tuple, np.ndarray)):
        raise TypeError(
            f"contours must be a list, tuple, or ndarray, "
            f"got {type(contours).__name__}"
        )

    # if no contours, it isn't in frame
    if len(contours) == 0:
        detection.in_frame = False
        return detection

    # look for the largest contour in the frame
    largest_area_px : float = 0
    largest_contour  = contours[0]

    for contour in contours:
        if not isinstance(contour, np.ndarray):
            raise TypeError("each contour must be a numpy.ndarray")

        if contour.ndim != 3 or contour.shape[1] != 1 or contour.shape[2] != 2:
            raise ValueError(
                "each contour must have shape (N, 1, 2), " f"got {contour.shape}"
            )

        area = cv2.contourArea(contour)

        if area >= largest_area_px:
            largest_area_px = area
            largest_contour = contour

    # if it's smaller than the min area, discard
    if largest_area_px < min_area_px:
        detection.in_frame = False
        return detection

    # else analyze as a circle
    center, radius = cv2.minEnclosingCircle(largest_contour)

    detection.in_frame = True
    detection.camera_pos_px = Point(center[0], center[1])
    detection.width_px = int(radius * 2)
    detection.area_px = int(np.pi * radius * radius)

    # convert to distance and angle
    detection.ang_from_bot_rad = calc_angle_from_screen_center(detection.camera_pos_px)
    detection.dis_from_bot_in = calc_distance_from_bot(known_width_in=known_width_in, percieved_width_px= detection.width_px)

    return detection


def get_list_detections(hsv_frame: np.ndarray, search_dict: dict) -> list[Detection]:
    '''search through the frame and return a list of a specific dataclass called a Detection'''
    detect_list = []

    search_list = [BALL_RED, HAT_BLUE, HAT_YELLOW, HAT_FUCHSIA, HAT_GREEN]

    for name in search_list:

        detection = get_detection_from_name(name, hsv_frame, search_dict)
        detect_list.append(detection)

    return detect_list


def example_vision_full_stack(
    frame_camera: np.ndarray, frame_field: np.ndarray, search_dict: dict
) -> np.ndarray:
    robot_pos = FIELD_GOALBOX_CENTER_BOTTOM
    robot_rad = BEARING_NORTH
    robot_color = YELLOW

    # put our bot at our goalbox
    frame_field = add_text_top(frame_field, "FIELD")
    frame_field = draw_robot_to_field(
        field_frame=frame_field,
        bearing_rad=robot_rad,
        pos_in=robot_pos,
        color=robot_color,
    )

    frame_hsv = get_hsv_frame(frame_camera.copy())

    # load the hsv bounds and filter
    hsv_lo = search_dict[BALL_RED][HSV_LO]
    hsv_hi = search_dict[BALL_RED][HSV_HI]
    frame_mask = get_mask_frame(frame_hsv.copy(), hsv_hi=hsv_hi, hsv_lo=hsv_lo)

    # determine the contours
    contours = get_contours(frame_mask=frame_mask)
    object_info = get_object_info_from_contours(contours, analyze_as_circle=True)

    # if it find's the ball, calculate and draw it
    if object_info["WIDTH_PX"] > 0:

        # determine the range and angle to the ball
        known_width_in = search_dict[BALL_RED][KNOWN_WIDTH]
        dis_from_bot_in = calc_distance_from_bot(
            known_width_in=known_width_in, percieved_width_px=object_info["WIDTH_PX"]
        )

        center_on_screen = Point(object_info["CENTER_X_PX"], object_info["CENTER_Y_PX"])
        ang_from_bot_rad = calc_angle_from_screen_center(point=center_on_screen)

        ball_pos_in: Point = convert_to_field(
            object_bearing_rad=ang_from_bot_rad,
            object_dis=dis_from_bot_in,
            robot_bearing_rad=robot_rad,
            robot_pos=robot_pos,
        )

        # add the ball to the field
        frame_field = draw_ball_to_field(frame_field, ball_pos_in)

        # draw arrows explaining
        frame_field = draw_top_down_arrows(
            field_frame=frame_field,
            ref_bearing_rad=robot_rad,
            ref_point_in=robot_pos,
            target_point_in=ball_pos_in,
        )

    ### Show User
    # combine frames together to more easily compare
    # frame mask is black and white but concat_frames needs color
    frame_mask = cv2.cvtColor(frame_mask, cv2.COLOR_GRAY2BGR)
    frame_mask = add_text_top(frame_mask, "MASK")
    frame_camera = add_text_top(frame_camera, "ORIGINAL")

    left_col = concat_frames(frame_camera, frame_mask, "DOWN")

    combined_frame = concat_frames(left_col, frame_field, "RIGHT")

    return combined_frame


