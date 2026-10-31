from constants import *
import cv2
import numpy as np
from classes import FieldState, DetectedObject, Point, get_point_int_tuple
from typing import Sequence
from variables import *
from constants import *
from tam_library import (
    append_dict_to_csv,
    load_image_as_frame,
    show_frame,
    debugprint,
    clear_csv,
)
from tam_library_front_and_top_down import (
    calc_distance_from_bot,
    calc_angle_from_screen_center,
)


def get_hsv_frame(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return hsv


def get_mask_frame(hsv_frame: np.ndarray, hsv_lo, hsv_hi) -> np.ndarray:
    mask = cv2.inRange(hsv_frame, lowerb=hsv_lo, upperb=hsv_hi)

    return mask


def get_fieldstate_from_frame(
    frame: np.ndarray,
    timestep: float = 0,
    append_to_dict: bool = False,
    csv_path: str = "",
) -> FieldState:
    """search the frame for each object and return a fieldstate"""

    this_frame_field_state = FieldState()

    # convert to hsv for processing
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if search_for_ball_red:
        ball_object = get_detected_object(
            object_name=BALL_RED, hsv_frame=hsv
        )
        if ball_object is not None:
            this_frame_field_state.ball_pos_in = ball_object.pos_wrt_bot

    if search_for_ball_yellow:
        ball_object = get_detected_object(
            object_name=BALL_YELLOW, hsv_frame=hsv, 
        )
        if ball_object is not None:
            pass  # TODO

    if search_for_hat_blue:
        hat_object = get_detected_object(
            object_name= HAT_BLUE, hsv_frame= hsv
        )
        if hat_object is not None:
            pass # TODO

    if append_to_dict:
        append_dict_to_csv(
            csv_file_path=csv_path, data=this_frame_field_state.to_dict()
        )

    return this_frame_field_state


def get_contours_from_mask(frame_mask: np.ndarray) -> tuple:
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

    return contours, hierarchy


def draw_contours(
    frame: np.ndarray,
    contours,
    color: tuple[int, int, int] = (0, 0, 0),
    thickness: int = 5,
) -> np.ndarray:
    """Draw all provided contours onto a BGR frame and return the frame."""
    if not isinstance(frame, np.ndarray):
        raise TypeError(
            f"frame must be numpy.ndarray, got {type(frame).__name__}"
        )

    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(
            f"frame must be a 3-channel BGR image, got shape {frame.shape}"
        )

    if not isinstance(contours, (list, tuple)):
        raise TypeError(
            f"contours must be a list or tuple, got {type(contours).__name__}"
        )

    if not isinstance(color, tuple) or len(color) != 3:
        raise TypeError("color must be a tuple of three integers: (B, G, R)")

    if not all(isinstance(value, (int, np.integer)) for value in color):
        raise TypeError("each color component must be an integer")

    if not isinstance(thickness, (int, np.integer)):
        raise TypeError(
            f"thickness must be an integer, got {type(thickness).__name__}"
        )

    if thickness < 1:
        raise ValueError(f"thickness must be at least 1, got {thickness}")

    if contours:
        cv2.drawContours(
            image=frame,
            contours=contours,
            contourIdx=-1,  # Draw all contours
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )

    return frame


def get_object_info_from_contours(
    contours,
    analyze_as_circle: bool = True,
) -> dict:
    """
    Analyze contours as circles or squares.

    Returns a dictionary containing object measurements in pixel units:
        - width: diameter for circles, bounding-box width for squares
        - area: contour area in pixels
        - center_x: horizontal center position
        - center_y: vertical center position

    If multiple contours are supplied, their measurements are combined into
    one bounding region and total area.
    """

    #dict_keys
    WIDTH_PX = "WIDTH_PX"
    AREA_PX = "AREA_PX"
    SHAPE = "SHAPE"
    CENTER_X_PX = "CENTER_X_PX"
    CENTER_Y_PX = "CENTER_Y_PX"

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
            SHAPE : "NO_SHAPE",
        }

    total_area = 0.0
    x_min = y_min = np.inf
    x_max = y_max = -np.inf

    for contour in contours:
        if not isinstance(contour, np.ndarray):
            raise TypeError("each contour must be a numpy.ndarray")

        if contour.ndim != 3 or contour.shape[1] != 1 or contour.shape[2] != 2:
            raise ValueError(
                "each contour must have shape (N, 1, 2), "
                f"got {contour.shape}"
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
        SHAPE : shape,
    }


def draw_object_to_frame(
    frame: np.ndarray,
    object_dict: dict,
    color: tuple[int, int, int] = (0, 0, 0),
    thickness: int = 5,
) -> np.ndarray:
    """
    Draw an object onto a BGR frame as either a circle or square.

    Expected object_dict keys:
        - width: diameter for a circle, side length for a square
        - area: object area in pixels
        - center_x: horizontal center position
        - center_y: vertical center position
        - shape: "circle" or "square"

    Returns:
        np.ndarray: The frame with the object drawn.
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(
            f"frame must be numpy.ndarray, got {type(frame).__name__}"
        )

    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(
            f"frame must be a 3-channel BGR image, got shape {frame.shape}"
        )

    if not isinstance(object_dict, dict):
        raise TypeError(
            f"object_dict must be dict, got {type(object_dict).__name__}"
        )

    required_keys = {"WIDTH_PX", "AREA_PX", "CENTER_X_PX", "CENTER_Y_PX", "SHAPE"}
    missing_keys = required_keys - object_dict.keys()
    if missing_keys:
        raise KeyError(
            f"object_dict is missing required keys: {sorted(missing_keys)}"
        )

    shape = str(object_dict["SHAPE"]).lower()
    if shape not in ("circle", "square", "no_shape"):
        raise ValueError(
            f"shape must be 'circle' or 'square', got {object_dict['SHAPE']!r}"
        )

    center_x = object_dict["CENTER_X_PX"]
    center_y = object_dict["CENTER_Y_PX"]
    width = object_dict["WIDTH_PX"]

    for name, value in (
        ("CENTER_X_PX", center_x),
        ("CENTER_Y_PX", center_y),
        ("WIDTH_PX", width),
    ):
        if not isinstance(value, (int, float, np.integer, np.floating)):
            raise TypeError(f"{name} must be a number, got {type(value).__name__}")

    if width <= 0:
        return frame

    center = (int(round(center_x)), int(round(center_y)))

    if shape == "circle":
        radius = int(round(width / 2))
        cv2.circle(
            img=frame,
            center=center,
            radius=radius,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )
    elif shape == "square":
        half_side = width / 2
        top_left = (
            int(round(center_x - half_side)),
            int(round(center_y - half_side)),
        )
        bottom_right = (
            int(round(center_x + half_side)),
            int(round(center_y + half_side)),
        )

        cv2.rectangle(
            img=frame,
            pt1=top_left,
            pt2=bottom_right,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )

    elif shape == "no_shape":
        pass

    return frame


def get_contours(hsv, hsv_hi, hsv_lo) -> Sequence[np.ndarray]:

    # create a mask using the hsv values
    #debugprint(f"hsv_hi: {hsv_hi}, hsv_lo: {hsv_lo}")
    mask = cv2.inRange(hsv, lowerb=hsv_lo, upperb=hsv_hi)


    # get the contours from the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def get_detected_object(
    object_name: str, hsv_frame
) -> DetectedObject | None:
    contours: Sequence[np.ndarray] = get_contours(
        hsv_frame,
        hsv_hi=search_dict[object_name][HSV_HI],
        hsv_lo=search_dict[object_name][HSV_LO],
    )
    best_contour, best_area = get_best_contour(contours)

    # if there is no contour, this object has not been detected, go to next object
    if best_contour is None:
        return None
    
    this_detect = DetectedObject()

    if search_dict[object_name][ANALYSIS_SHAPE] == CIRC:
        (x, y), radius = cv2.minEnclosingCircle(best_contour)
        this_detect.center_pos_on_screen_px = Point(x, y)
        this_detect.width_px = int(radius * 2)
        this_detect.area_px = int(np.pi * radius * radius)

    elif search_dict[object_name][ANALYSIS_SHAPE] == RECT:
        left_x, top_y, width, height = cv2.boundingRect(best_contour)
        x_center = int(left_x + width / 2)
        y_center = int(top_y + height / 2)

        this_detect.center_pos_on_screen_px = Point(x_center, y_center)
        this_detect.width_px = width
        this_detect.area_px = width * height

    else:
        print("couldn't find analysis shape, expected RECT or CIRC")

    # convert to top down
    this_detect.distance_from_bot = calc_distance_from_bot(
        known_width_in=search_dict[object_name][KNOWN_WIDTH],
        percieved_width_px=this_detect.width_px,
    )
    this_detect.bearing_rad = calc_angle_from_screen_center(
        this_detect.center_pos_on_screen_px
    )

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


def annotate_cam_frame(
    cam_frame: np.ndarray, obj: DetectedObject, obj_name: str
) -> np.ndarray:

    shape = search_dict[obj_name][ANALYSIS_SHAPE]

    # draw a small circle at the center
    cam_frame = cv2.circle(
        img=cam_frame,
        center=get_point_int_tuple(obj.center_pos_on_screen_px),
        radius=3,
        color=search_dict[obj_name][DRAW_COLOR],
    )

    # then draw the bounding shape (circle or rectangle)
    if shape == CIRC:
        cam_frame = cv2.circle(
            img=cam_frame,
            center=get_point_int_tuple(obj.center_pos_on_screen_px),
            radius=int(obj.width_px / 2),
            color=search_dict[obj_name][DRAW_COLOR],
            thickness=PIXELS_PER_INCH,
        )

    return cam_frame


def update_field_state_with_object(
        obj: DetectedObject,
        field_state: FieldState,
        is_goalpost: bool = False) -> FieldState:

    # update the ROBOT's position wrt the fixed goalpost
    if is_goalpost:
        pass

    # update the OBJECT's position wrt the robot
    else:
        # TODO
        object_x = field_state.our_bot_pos_in.x
        pass



    return field_state



def testing_search_frame():

    image_name = "tennis_ball_48in"

    image_path = f"training_data/{image_name}.png"

    csv_path = FIELD_STATES + "/" + image_name + ".csv"

    clear_csv(csv_path)

    cam_frame = load_image_as_frame(image_path)

    # convert to hsv for processing
    hsv = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2HSV)
    # show_frame(hsv)

    field_state = FieldState()

    search_for: str = BALL_YELLOW

    obj = get_detected_object(
        hsv_frame=hsv, object_name=search_for
    )
    if obj is None:
        return

    
    # draw a bounding shape around the detected object
    cam_frame = annotate_cam_frame(
        cam_frame=cam_frame, obj=obj, obj_name=search_for
    )
    print(obj)

    # add the object information to the field state
    

    show_frame(cam_frame)
    # field_state = get_fieldstate_from_frame(frame=cam_frame, append_to_dict=True, csv_path=csv_path)

    # print(field_state)


if __name__ == "__main__":
    testing_search_frame()