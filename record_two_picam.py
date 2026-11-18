import time
from datetime import datetime

import cv2
import numpy as np
from tam_switches import get_switch_status, setup_switches
from tam_binocular import setup_left_right_cams, get_left_right_frames
from picamera2 import Picamera2
from typing import Optional


def record_picam_left_right(duration_sec : int = 20, frames_per_sec : int = 30):
    '''
    Record two picameras on a raspberry pi when the recording switch is on. 
    Saves to two files with ISO name structures YYYY_MM_DD_T_HH_MM_SS_LEFT.mp4 or ...RIGHT.mp4
    '''

    setup_switches()
    picam_left, picam_right = setup_left_right_cams()

    picam_left : Picamera2
    picam_right : Picamera2

    def to_bgr(frame: np.ndarray) -> np.ndarray:
        # Drop the alpha/padding channel if present (e.g. XRGB8888 -> 3 channels)
        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = frame[:, :, :3]
        return np.ascontiguousarray(frame)

    def open_writer(path: str, frame: np.ndarray) -> cv2.VideoWriter:
        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        return cv2.VideoWriter(path, fourcc, frames_per_sec, (width, height))

    writer_left: Optional[cv2.VideoWriter] = None
    writer_right: Optional[cv2.VideoWriter] = None
    frames_written = 0
    total_frames = duration_sec * frames_per_sec
    frame_interval = 1.0 / frames_per_sec
    next_frame_time = time.monotonic()

    try:
        while True:
            frame_left, frame_right = get_left_right_frames(picam_left, picam_right)
            frame_left : np.ndarray
            frame_right : np.ndarray

            recording_on = bool(get_switch_status("toggle_recording"))

            if recording_on:
                frame_left = to_bgr(frame_left)
                frame_right = to_bgr(frame_right)

                # Start a new clip if none is open
                if writer_left is None or writer_right is None:
                    timestamp = datetime.now().strftime("%Y_%m_%d_T_%H_%M_%S")
                    writer_left = open_writer(f"{timestamp}_LEFT.mp4", frame_left)
                    writer_right = open_writer(f"{timestamp}_RIGHT.mp4", frame_right)
                    frames_written = 0
                    next_frame_time = time.monotonic()

                writer_left.write(frame_left)
                writer_right.write(frame_right)
                frames_written += 1

                if frames_written >= total_frames:
                    writer_left.release()
                    writer_right.release()
                    writer_left = writer_right = None
            else:
                if writer_left is not None:
                    writer_left.release()
                    writer_left = None
                if writer_right is not None:
                    writer_right.release()
                    writer_right = None

            # Pace the loop to the requested frame rate
            next_frame_time += frame_interval
            sleep_time = next_frame_time - time.monotonic()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_frame_time = time.monotonic()  # fell behind; resync

    except KeyboardInterrupt:
        pass
    finally:
        if writer_left is not None:
            writer_left.release()
        if writer_right is not None:
            writer_right.release()
        picam_left.stop()
        picam_right.stop()