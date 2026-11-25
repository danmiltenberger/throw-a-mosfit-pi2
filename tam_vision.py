## all the functions that convert the camera frame into bools, floats, etc

import cv2
import numpy as np
import math
from tam_classes import FieldState, Point, Detection, CameraState, Settings, DualCameraState
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
    draw_ball_to_field,
    draw_top_down_arrows,
    draw_object_to_frame,
    add_text_top,
    draw_robot_to_field
)
from tam_frame import concat_frames
from typing import Sequence
from tam_triangulate import triangulate_object_wrt_bot


def get_hsv_frame(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return hsv


def clean_mask(mask: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # remove speckle
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # fill small holes
    return mask


def get_red_mask(frame: np.ndarray,
                 min_saturation: int = 120,
                 min_value: int = 70,
                 hue_width: int = 10,
                 clean: bool = True,
                 is_hsv: bool = False) -> np.ndarray:
    '''
    Return a binary mask (uint8, 0 or 255) of red pixels.
    Input is a BGR frame by default, or an HSV frame if is_hsv=True.
    '''
    if is_hsv:
        hsv = frame
    else:
        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = frame[:, :, :3]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower1 = np.array([0, min_saturation, min_value])
    upper1 = np.array([hue_width, 255, 255])
    lower2 = np.array([179 - hue_width, min_saturation, min_value])
    upper2 = np.array([179, 255, 255])

    mask = cv2.bitwise_or(cv2.inRange(hsv, lower1, upper1),
                          cv2.inRange(hsv, lower2, upper2))

    return clean_mask(mask) if clean else mask


def get_mask_frame(hsv_frame: np.ndarray, hsv_lo, hsv_hi, is_red: bool = False) -> np.ndarray:
    if is_red:
        # Red wraps around the hue axis, so hsv_lo / hsv_hi are ignored
        return get_red_mask(hsv_frame, is_hsv=True)

    mask = cv2.inRange(hsv_frame, lowerb=hsv_lo, upperb=hsv_hi)
    return clean_mask(mask)


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


def create_mask(obj_name: str, hsv_frame: np.ndarray, search_dict: dict) -> np.ndarray:
    hsv_lo = search_dict[obj_name][HSV_LO]
    hsv_hi = search_dict[obj_name][HSV_HI]
    is_red = obj_name == BALL_RED
    return get_mask_frame(hsv_frame=hsv_frame, hsv_hi=hsv_hi, hsv_lo=hsv_lo, is_red=is_red)


def validate_contours(contours) -> None:
    if contours is None:
        raise TypeError("contours must not be None")

    if not isinstance(contours, (list, tuple, np.ndarray)):
        raise TypeError(
            f"contours must be a list, tuple, or ndarray, "
            f"got {type(contours).__name__}"
        )

    for contour in contours:
        if not isinstance(contour, np.ndarray):
            raise TypeError("each contour must be a numpy.ndarray")

        if contour.ndim != 3 or contour.shape[1] != 1 or contour.shape[2] != 2:
            raise ValueError(
                f"each contour must have shape (N, 1, 2), got {contour.shape}"
            )


def filter_contours_by_area(contours, min_area_px: int) -> list:
    return [c for c in contours if cv2.contourArea(c) >= min_area_px]


def contour_to_detection(obj_name: str, contour: np.ndarray) -> Detection:
    (cx, cy), radius = cv2.minEnclosingCircle(contour)

    return Detection(
        name=obj_name,
        in_frame=True,
        camera_pos_px=Point(cx, cy),
        width_px=int(radius * 2),
        area_px=int(np.pi * radius * radius),
    )


def sort_top_to_bottom(detections: list[Detection]) -> list[Detection]:
    # smaller y = higher on screen
    return sorted(detections, key=lambda d: d.camera_pos_px.y)


def get_detections_from_name(
    obj_name: str,
    hsv_frame: np.ndarray,
    search_dict: dict,
    max_detections: int,
) -> list[Detection]:
    """Return up to max_detections detections, highest on screen first.
    Returns an empty list if nothing is found."""
    min_area_px = int(search_dict[obj_name][MIN_AREA_PX])

    mask_frame = create_mask(obj_name, hsv_frame, search_dict)
    contours = get_contours(mask_frame)
    validate_contours(contours)

    valid_contours = filter_contours_by_area(contours, min_area_px)
    detections = [contour_to_detection(obj_name, c) for c in valid_contours]

    return sort_top_to_bottom(detections)[:max_detections]


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


def get_dual_camerastate(
        frame_left : np.ndarray, 
        frame_right: np.ndarray, 
        search_dict: dict, 
        match_set : Settings, 
        search_list : list[str] = [BALL_RED, HAT_BLUE, HAT_YELLOW, HAT_FUCHSIA, HAT_GREEN]) -> DualCameraState:
    '''get the left and right camerastates from the left and right frames. Defaults to looking for all objects but optionally search for less'''

    our_left_is_green = match_set.left_is_green


    cs_left = get_camerastate_filtered(
        search_list= search_list,
        search_dict= search_dict,
        frame_camera= frame_left,
        is_left= True,
        our_left_is_green= our_left_is_green
    )

    cs_right = get_camerastate_filtered(
        search_list= search_list,
        search_dict= search_dict,
        frame_camera= frame_right,
        is_left= False,
        our_left_is_green= our_left_is_green
    )

    dual_cam = DualCameraState()
    dual_cam.left = cs_left
    dual_cam.right = cs_right

    return dual_cam






def get_camerastate(
        frame_camera: np.ndarray, 
        search_dict:dict, 
        is_left: bool = True,
        our_left_is_green : bool = True
        ) -> CameraState:
    '''wrapper for get_camerastate_filtered but includes all'''

    search_list = [BALL_RED, HAT_BLUE, HAT_YELLOW, HAT_FUCHSIA, HAT_GREEN]

    cs = get_camerastate_filtered(
        search_list= search_list,
        search_dict= search_dict,
        frame_camera= frame_camera,
        is_left= is_left,
        our_left_is_green= our_left_is_green
    )

    return cs


def get_camerastate_filtered(
        frame_camera: np.ndarray, 
        search_dict:dict, 
        search_list: list[str], 
        is_left: bool = True,
        our_left_is_green : bool = True
        ) -> CameraState:
    '''search the camera for the specified search list instead of doing the entire thing'''

    cs = CameraState()
    cs.is_left_camera = is_left

    hsv_frame = get_hsv_frame(frame_camera.copy())

    if BALL_RED in search_list:
        ball_detect = get_detections_from_name(hsv_frame= hsv_frame, search_dict= search_dict, max_detections=1, obj_name=BALL_RED)[0]
        if ball_detect.in_frame:
            cs.ball_in_frame = True
            cs.ball_pos_px = ball_detect.camera_pos_px
            cs.ball_width_px = ball_detect.width_px

    if HAT_YELLOW in search_list:
        tbot_detect_list = get_detections_from_name(hsv_frame= hsv_frame, search_dict= search_dict, max_detections=1, obj_name=HAT_YELLOW)
        if len(tbot_detect_list) == 0:
            pass
        else: 
            tbot_detect = tbot_detect_list[0]
            if tbot_detect.in_frame:
                cs.tbot_in_frame = True
                cs.tbot_pos_px = tbot_detect.camera_pos_px
                cs.tbot_width_px = tbot_detect.width_px

    if HAT_BLUE in search_list:
        tbot_detect_list = get_detections_from_name(hsv_frame= hsv_frame, search_dict= search_dict, max_detections=1, obj_name=HAT_BLUE)
        if len(tbot_detect_list) == 0:
            pass
        else: 
            tbot_detect = tbot_detect_list[0]
            if tbot_detect.in_frame:
                cs.tbot_in_frame = True
                cs.tbot_pos_px = tbot_detect.camera_pos_px
                cs.tbot_width_px = tbot_detect.width_px

    # green and purple might have two detections
    if HAT_GREEN in search_list:
        green_detect_list = get_detections_from_name(hsv_frame= hsv_frame, search_dict= search_dict, max_detections=2, obj_name=HAT_GREEN)

        len_list = len(green_detect_list)
        if len_list == 0:
            pass
        if len_list >= 1:
            top_green_detect = green_detect_list[0]
            if top_green_detect.in_frame:
                cs.gp_green_up_in_frame = True
                cs.gp_green_up_pos_px = top_green_detect.camera_pos_px
                cs.gp_green_up_width_px = top_green_detect.width_px
        
        if len_list >= 2:
            bot_green_detect = green_detect_list[1]
            if bot_green_detect.in_frame:
                cs.gp_green_dw_in_frame = True
                cs.gp_green_dw_pos_px = bot_green_detect.camera_pos_px
                cs.gp_green_dw_width_px = bot_green_detect.width_px

    if HAT_FUCHSIA in search_list:
        purpl_detect_list = get_detections_from_name(hsv_frame= hsv_frame, search_dict= search_dict, max_detections=2, obj_name=HAT_FUCHSIA)

        len_list = len(purpl_detect_list)
        if len_list == 0:
            pass
        if len_list >= 1:
            top_purpl_detect = purpl_detect_list[0]
            if top_purpl_detect.in_frame:
                cs.gp_purpl_up_in_frame = True
                cs.gp_purpl_up_pos_px = top_purpl_detect.camera_pos_px
                cs.gp_purpl_up_width_px = top_purpl_detect.width_px
        
        if len_list >= 2:
            bot_purpl_detect = purpl_detect_list[1]
            if bot_purpl_detect.in_frame:
                cs.gp_purpl_dw_in_frame = True
                cs.gp_purpl_dw_pos_px = bot_purpl_detect.camera_pos_px
                cs.gp_purpl_dw_width_px = bot_purpl_detect.width_px

    cs = determine_goal_in_frame(cs, our_left_is_green)

    return cs





def determine_goal_in_frame(cs : CameraState, our_left_is_green: bool) -> CameraState:
    '''determine whos goal if any is in frame'''
    # if there is a green and purple in frame
    if (cs.gp_green_up_in_frame or cs.gp_green_dw_in_frame) and (cs.gp_purpl_up_in_frame or cs.gp_purpl_dw_in_frame):

        # get the green goalpost
        if cs.gp_green_up_in_frame:
            green_goal_pos_px = cs.gp_green_up_pos_px
        else:
            green_goal_pos_px = cs.gp_green_dw_pos_px

        # get the purple goalpost
        if cs.gp_purpl_up_in_frame:
            purpl_goal_pos_px = cs.gp_purpl_up_pos_px
        else:
            purpl_goal_pos_px = cs.gp_purpl_dw_pos_px
 
        # if green is more left than purple
        if green_goal_pos_px.x < purpl_goal_pos_px.x:
            is_green_purple = True
        else:
            is_green_purple = False

        if our_left_is_green:
            if is_green_purple:
                # opponent goal
                cs.their_goal_in_frame = True
                return cs
            else:
                # our goal
                cs.our_goal_in_frame = True
                return cs
        else:
            if is_green_purple:
                # our goal
                cs.our_goal_in_frame = True
                return cs
            else:
                # opponent goal
                cs.their_goal_in_frame = True
                return cs
    else:
        # unable to determine goal, default is false so we're good
        return cs






def get_fieldstate(
        cs_left: CameraState, 
        cs_right: CameraState, 
        prev_fs: FieldState,) -> FieldState:
    '''given two camera states, determine the state of the field by 
    first updating the bot's pose with respect to the fixed goalposts, then 
    updating the position of other objects with respect to the bot's pose'''

    def get_ball_pos_on_field(fs: FieldState) -> FieldState:

        if cs_left.ball_in_frame and cs_right.ball_in_frame:
            ball_dis, ball_rad = triangulate_object_wrt_bot(cs_left.ball_pos_px, cs_right.ball_pos_px)

            fs.ball_pos_in = convert_to_field(
                object_bearing_rad=ball_rad,
                object_dis=ball_dis,
                robot_bearing_rad=fs.our_bot_bearing_rad,
                robot_pos=fs.our_bot_pos_in,
            )
        else:
            fs.ball_pos_in = fs.ball_pos_in
        return fs


    def get_opponent_pos_on_field(fs: FieldState) -> FieldState:
        if cs_left.tbot_in_frame and cs_right.tbot_in_frame:
            opponent_dis, opponent_rad = triangulate_object_wrt_bot(cs_left.tbot_pos_px, cs_right.tbot_pos_px)
            fs.their_bot_pos_in = convert_to_field(
                object_bearing_rad=opponent_rad,
                object_dis=opponent_dis,
                robot_bearing_rad=fs.our_bot_bearing_rad,
                robot_pos=fs.our_bot_pos_in,
            )
        else:
            fs.their_bot_pos_in = prev_fs.their_bot_pos_in
        return fs

    

    fs = prev_fs
    fs = get_opponent_pos_on_field(fs)
    fs = get_ball_pos_on_field(fs)

    return fs