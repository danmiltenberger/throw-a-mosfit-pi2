from tam_library_draw_field import draw_gate, inches_to_screen
from tam_library import load_image_as_frame
from constants_points import *
import cv2
import numpy as np
from classes import Point
import time

def animate_gate(
    frame: np.ndarray,
    start_angle_deg: float,
    swing_angle_deg: float,
    start_position: Point,
    duration: float,
    fps: float = 60.0,
    window_name: str = "Gate",
) -> np.ndarray:
    """Animate a gate rotating around a fixed pivot.

    Args:
        frame: Background image; left unchanged.
        start_angle_deg: Initial angle: 0=east, 90=north, -90=south.
        swing_angle_deg: Total rotation; positive=counterclockwise.
        start_position: Fixed pivot point with .x and .y attributes.
        duration: Total animation duration in seconds.
        fps: Target display frame rate.
        window_name: OpenCV display window name.

    Returns:
        The last rendered frame.

    Press Escape to stop the animation early.
    """
    if duration < 0:
        raise ValueError("duration must be nonnegative")
    if fps <= 0:
        raise ValueError("fps must be positive")

    background = frame.copy()
    frame_interval = 1.0 / fps
    started_at = time.perf_counter()
    next_frame_at = started_at

    while True:
        now = time.perf_counter()
        progress = (
            1.0
            if duration == 0
            else min((now - started_at) / duration, 1.0)
        )

        angle_deg = start_angle_deg + swing_angle_deg * progress

        # draw_gate uses clockwise-positive image coordinates.
        bearing_rad = -np.deg2rad(angle_deg)

        # Draw on a fresh background to avoid leaving trails.
        rendered = draw_gate(
            background.copy(),
            start_position,
            bearing_rad,
        )
        cv2.imshow(window_name, rendered)

        if cv2.waitKey(1) & 0xFF == 27:
            break

        if progress >= 1.0:
            break

        next_frame_at += frame_interval
        # Schedule the final frame at the requested end time.
        next_frame_at = min(next_frame_at, started_at + duration)
        delay = next_frame_at - time.perf_counter()
        if delay > 0:
            time.sleep(delay)

    return rendered


frame = load_image_as_frame("field_pngs/field_black.png")
pivot = FIELD_CENTER

pivot_px = inches_to_screen(pivot)


last_frame = animate_gate(
    frame=frame,
    start_angle_deg=-45,
    swing_angle_deg=90,
    start_position=pivot_px,
    duration=2.0,
)

# Keep the final frame visible until a key is pressed.
cv2.waitKey(0)
cv2.destroyAllWindows()