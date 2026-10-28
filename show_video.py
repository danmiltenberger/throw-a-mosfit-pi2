import math
import time
from typing import Callable, Optional
from tam_library import load_video_as_list_of_frames

import cv2
import numpy as np


def show_video(
    vid_path: str,
    window_name: str = "window",
    fps: int = 30,
    frame_to_frame: Optional[
        Callable[[np.ndarray], np.ndarray]
    ] = None,
):
    if fps <= 0:
        raise ValueError("fps must be greater than zero.")

    print(f"loading frames from {vid_path}")
    list_frames = load_video_as_list_of_frames(vid_path)

    frame_duration = 1.0 / fps

    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    try:
        for frame in list_frames:
            frame_deadline = time.perf_counter() + frame_duration

            if frame_to_frame is not None:
                # Protect the loaded frame if the callback modifies it in place.
                display_frame = frame_to_frame(frame.copy())
            else:
                display_frame = frame

            cv2.imshow(winname=window_name, mat=display_frame)

            while True:
                remaining = frame_deadline - time.perf_counter()
                delay_ms = max(1, min(10, math.ceil(remaining * 1000)))

                key = cv2.waitKey(delay_ms) & 0xFF

                if key in (27, ord("q")):
                    return

                if cv2.getWindowProperty(
                    window_name, cv2.WND_PROP_VISIBLE
                ) < 1:
                    return

                if time.perf_counter() >= frame_deadline:
                    break
    finally:
        try:
            cv2.destroyWindow(window_name)
        except cv2.error:
            pass

def to_black_and_white(frame: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


# Show grayscale video.
show_video(
    "training_data/red_ball_vid.h264",
    fps=30,
    frame_to_frame=to_black_and_white,
)
