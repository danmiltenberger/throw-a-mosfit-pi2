import math
import cv2
import numpy as np
from classes import Point, FieldState, get_point_int_tuple
from draw_field import (
    get_field_frame,
    inches_to_screen,
    convert_to_px,
    draw_notched_rectangle,
)
from tam_library import show_frame, debugprint
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


def draw_outlined_circle(
    image,
    center_x,
    center_y,
    radius,
    color=(255, 255, 255),
    border_thickness=1,
):
    """
    Draw a filled circle with a thin black outline.

    Parameters
    ----------
    image : np.ndarray
        Destination image; modified in place.
    center_x, center_y : float
        Circle center in image coordinates, in pixels.
    radius : float
        Circle radius in pixels; must be positive.
    color : tuple or int
        OpenCV BGR fill color, or a scalar for a grayscale image.
    border_thickness : int
        Black outline width in pixels; must be at least 1.

    Returns
    -------
    np.ndarray
        The modified input image.
    """
    if not all(np.isfinite(v) for v in (center_x, center_y, radius)):
        raise ValueError("Center coordinates and radius must be finite.")
    if radius <= 0:
        raise ValueError("radius must be positive.")
    if not isinstance(border_thickness, (int, np.integer)) or border_thickness < 1:
        raise ValueError("border_thickness must be a positive integer.")

    # Preserve subpixel coordinates until rasterization.
    shift = 8
    scale = 1 << shift
    center = (
        int(round(center_x * scale)),
        int(round(center_y * scale)),
    )
    scaled_radius = int(round(radius * scale))

    cv2.circle(
        image,
        center,
        scaled_radius,
        color=color,
        thickness=cv2.FILLED,
        lineType=cv2.LINE_AA,
        shift=shift,
    )

    black = 0 if image.ndim == 2 else (0,) * image.shape[2]

    cv2.circle(
        image,
        center,
        scaled_radius,
        color=black,
        thickness=int(border_thickness),
        lineType=cv2.LINE_AA,
        shift=shift,
    )

    return image


def draw_field_from_field_state(
    field_frame: np.ndarray, state: FieldState
) -> np.ndarray:

    if draw_ball_red:
        ball_pos_px = inches_to_screen(state.ball_pos_in)

        field_frame = draw_outlined_circle(
            image=field_frame,
            center_x=int(ball_pos_px.x),
            center_y=int(ball_pos_px.y),
            color=RED,
            radius=convert_to_px(BALL_RED_RADIUS_IN),
        )

    # FIXME
    OUR_TEAM_COLOR = YELLOW

    if draw_our_bot:

        our_bot_pos_px = inches_to_screen(state.our_bot_pos_in)

        field_frame = draw_notched_rectangle(
            image=field_frame,
            center_x=int(our_bot_pos_px.x),
            top_y=int(our_bot_pos_px.y - convert_to_px(BOT_RADIUS_IN)),
            width=convert_to_px(BOT_RADIUS_IN) * 2,
            height=convert_to_px(BOT_RADIUS_IN) * 2,
            base_length=convert_to_px(BALL_RED_RADIUS_IN) * 2,
            angle_deg=90,
            color=OUR_TEAM_COLOR,
            rotation_deg=math.degrees(state.our_bot_bearing_rad),
            border_thickness=1,
        )

    THEIR_TEAM_COLOR = BLUE
    if draw_their_bot:
        their_bot_pos_x = inches_to_screen(state.their_bot_pos_in)

        field_frame = draw_notched_rectangle(
            image=field_frame,
            center_x=int(their_bot_pos_x.x),
            top_y=int(their_bot_pos_x.y - convert_to_px(BOT_RADIUS_IN)),
            width=convert_to_px(BOT_RADIUS_IN) * 2,
            height=convert_to_px(BOT_RADIUS_IN) * 2,
            base_length=convert_to_px(BALL_RED_RADIUS_IN) * 2,
            angle_deg=90,
            color=THEIR_TEAM_COLOR,
            rotation_deg=math.degrees(state.their_bot_bearing_rad),
            border_thickness=1,
        )

    return field_frame


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
