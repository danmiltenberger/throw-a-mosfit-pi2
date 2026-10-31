'''collection of fxns to determine if items are within zones, etc, also shows frames to user'''


from classes import Point, Line
import numpy as np
import cv2
from tam_library import load_image_as_frame, show_frame
from tam_library_draw_field import get_field_frame
from tam_library_lcd import lcd_simulated


def is_on_line(point_in_q: Point, line: Line) -> bool:
    # check if a given point lies on the line between points

    # equation of line: y = mx + b
    rise = line.pt2.y - line.pt1.y
    run = line.pt2.x - line.pt1.x
    m = rise / run

    # solve for b (y intercept) using one of the poitns
    b = line.pt1.y - m * line.pt1.x

    # check if new point lies along the line
    calc_y = m * point_in_q.x + b

    # round to nearest whole num
    calc_y = round(calc_y)
    given_y = round(point_in_q.y)

    if calc_y == given_y:
        return True
    else:
        return False


def is_within_rect(point_in_q: Point, top_left: Point, bot_right: Point) -> bool:
    # check x

    within_x: bool = False
    within_y: bool = False

    if top_left.x <= point_in_q.x <= bot_right.x:
        within_x = True

    if bot_right.y <= point_in_q.y <= top_left.y:
        within_y = True

    if within_x and within_y:
        return True
    else:
        return False


def is_within_circ(point_in_q: Point, circle_center: Point, cicle_rad: float) -> bool:
    """Return True if the point is inside or on the circle."""
    if cicle_rad < 0:
        raise ValueError("Circle radius must be non-negative.")

    dx = point_in_q.x - circle_center.x
    dy = point_in_q.y - circle_center.y

    return dx * dx + dy * dy <= cicle_rad * cicle_rad


def concat_frames(
    orig_frame: np.ndarray,
    added_frame: np.ndarray,
    added_dir: str = "RIGHT",
) -> np.ndarray:
    """Combine frames side by side or vertically.

    The added frame is resized to match the original frame's height for
    horizontal placement, or width for vertical placement.
    """
    if orig_frame is None or added_frame is None:
        raise ValueError("orig_frame and added_frame must not be None")

    direction = added_dir.upper()
    orig_h, orig_w = orig_frame.shape[:2]
    added_h, added_w = added_frame.shape[:2]

    def resize_to_dimension(frame: np.ndarray, target_size: tuple[int, int]) -> np.ndarray:
        target_w, target_h = target_size
        interp = cv2.INTER_AREA if (target_w < frame.shape[1] or target_h < frame.shape[0]) else cv2.INTER_CUBIC
        return cv2.resize(frame, (target_w, target_h), interpolation=interp)

    if direction in ("LEFT", "RIGHT"):
        # Horizontal concatenation: added frame must match original height.
        if added_h != orig_h:
            scale = orig_h / added_h
            new_w = max(1, round(added_w * scale))
            added_frame = resize_to_dimension(added_frame, (new_w, orig_h))

        # Correct any off-by-one difference after rounding.
        if added_frame.shape[0] != orig_h:
            pad = orig_h - added_frame.shape[0]
            added_frame = cv2.copyMakeBorder(
                added_frame, 0, pad, 0, 0, cv2.BORDER_CONSTANT
            )

        if direction == "LEFT":
            return np.concatenate((added_frame, orig_frame), axis=1)
        return np.concatenate((orig_frame, added_frame), axis=1)

    if direction in ("TOP", "UP", "BOTTOM", "DOWN"):
        # Vertical concatenation: added frame must match original width.
        if added_w != orig_w:
            scale = orig_w / added_w
            new_h = max(1, round(added_h * scale))
            added_frame = resize_to_dimension(added_frame, (orig_w, new_h))

        # Correct any off-by-one difference after rounding.
        if added_frame.shape[1] != orig_w:
            pad = orig_w - added_frame.shape[1]
            added_frame = cv2.copyMakeBorder(
                added_frame, 0, 0, 0, pad, cv2.BORDER_CONSTANT
            )

        if direction in ("TOP", "UP"):
            return np.concatenate((added_frame, orig_frame), axis=0)
        return np.concatenate((orig_frame, added_frame), axis=0)

    raise ValueError(
        "added_dir must be one of: 'LEFT', 'RIGHT', 'TOP'/'UP', or 'BOTTOM'/'DOWN'"
    )


def get_dashboard(
        camera_frame: np.ndarray, 
        field_frame: np.ndarray,
        lcd_frame : np.ndarray | None = None, ) -> np.ndarray:


    if lcd_frame is not None:
        dashboard_frame = concat_frames(camera_frame, lcd_frame, "DOWN")
    else:
        dashboard_frame = camera_frame

    dashboard_frame = concat_frames(dashboard_frame, field_frame, "RIGHT")

    return dashboard_frame



def test_get_dashboard():
    camera_frame = load_image_as_frame("training_data/red_ball_centerframe.png")
    field_frame = get_field_frame()
    lcd_frame = lcd_simulated(["line 1", "line 2", "line 3", "line 4"])

    dashboard_frame = get_dashboard(field_frame= field_frame, camera_frame= camera_frame, lcd_frame= lcd_frame)
    #dashboard_frame = get_dashboard(field_frame= field_frame, camera_frame= camera_frame)

    show_frame(frame= dashboard_frame, window_name= "demo dashboard")


if __name__ == "__main__":
    test_get_dashboard()
