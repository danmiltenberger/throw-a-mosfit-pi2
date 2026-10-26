import math
import cv2
import numpy as np
from classes import Point, FieldState, get_point_int_tuple

from tam_library import show_frame, debugprint
from tam_library_draw_field import get_field_frame, draw_outlined_circle, draw_field_from_field_state
from constants import *
from variables import *


def draw_arrow(
    frame: np.ndarray,
    start: Point,
    distance: float | None = None,
    angle_rad: float | None = None,
    end: Point | None = None,
    color=(0, 255, 0),
    thickness: int = 2,
    tip_size: int = 10,
):
    """Draw an arrow from `start`, optionally with a rotated label.

    Requires either:
      - `distance` AND `angle_rad`, or
      - `end`

    Args:
        frame: BGR image to draw on.
        start: Point with `.x` and `.y` attributes.
        distance: Arrow length in pixels.
        angle_rad: Direction angle in radians, using image coordinates.
        end: Optional Point defining the arrow tip.
        color: BGR color.
        thickness: Line thickness.
        tip_size: Arrowhead size in pixels.


    Returns:
        The modified frame.
    """
    has_vector = distance is not None and angle_rad is not None
    has_end = end is not None

    if has_vector == has_end:
        raise ValueError(
            "Provide either (distance AND angle_rad) OR end, but not both."
        )

    sx, sy = int(start.x), int(start.y)

    if has_end:
        ex, ey = int(end.x), int(end.y)
        angle_rad = math.atan2(ey - sy, ex - sx)
    else:
        if distance is float:
            ex = sx + int(round(distance * math.cos(angle_rad)))
            ey = sy + int(round(distance * math.sin(angle_rad)))
        else:
            raise ValueError(f"{distance} is not float")

    frame = cv2.arrowedLine(
        img=frame,
        pt1=(sx, sy),
        pt2=(ex, ey),
        color=color,
        thickness=thickness,
        tipLength=max(0.03, tip_size / max(1.0, math.hypot(ex - sx, ey - sy))),
    )

    return frame






if __name__ == "__main__":
    field_frame = get_field_frame()

    state = FieldState()
    state.ball_pos_in = Point(48, 132)
    state.our_bot_pos_in = Point(53, 12)
    state.our_bot_bearing_rad = np.pi / 4

    state.their_bot_pos_in = Point(72, 72)
    state.their_bot_bearing_rad = np.pi


    field_frame = draw_field_from_field_state(field_frame=field_frame, state=state)

    show_frame(field_frame)
