## all the functions that convert the camera frame into bools, floats, etc

import cv2
import numpy as np


def get_hsv_frame(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return hsv


def get_mask_frame(hsv_frame: np.ndarray, hsv_lo, hsv_hi) -> np.ndarray:
    mask = cv2.inRange(hsv_frame, lowerb=hsv_lo, upperb=hsv_hi)

    return mask


def get_contours(frame_mask: np.ndarray) -> tuple:
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


