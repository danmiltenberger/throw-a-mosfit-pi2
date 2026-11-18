import time
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
from tam_switches import get_switch_status, setup_switches
from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_lcd import write_lcd_lines
from picamera2 import Picamera2

LCD_WIDTH = 20
LCD_ROWS = 4
SAVED_MESSAGE_SEC = 3  # how long the "Files saved" screen stays up before status resumes


def record_picam_left_right(duration_sec : int = 20, frames_per_sec : int = 30):
    '''
    Record two picameras on a raspberry pi when the recording switch is on. 
    Saves to two files with ISO name structures YYYY_MM_DD_T_HH_MM_SS_LEFT.mp4 or ...RIGHT.mp4
    '''

    setup_switches()
    picam_left, picam_right = setup_left_right_cams()

    picam_left : Picamera2
    picam_right : Picamera2

    writer_left: Optional[cv2.VideoWriter] = None
    writer_right: Optional[cv2.VideoWriter] = None
    timestamp = ""
    frames_written = 0
    total_frames = duration_sec * frames_per_sec
    frame_interval = 1.0 / frames_per_sec
    next_frame_time = time.monotonic()
    saved_until = 0.0
    last_lcd: Optional[list] = None

    def lcd(lines: list):
        # Pad/truncate to 4 rows x 20 chars, and only write when the text changes
        # (avoids hammering the LCD at every video frame)
        nonlocal last_lcd
        padded = (list(lines) + [""] * LCD_ROWS)[:LCD_ROWS]
        fitted = [line[:LCD_WIDTH].ljust(LCD_WIDTH) for line in padded]
        if fitted != last_lcd:
            write_lcd_lines(fitted)
            last_lcd = fitted

    def to_bgr(frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = frame[:, :, :3]
        return np.ascontiguousarray(frame)

    def open_writer(path: str, frame: np.ndarray) -> cv2.VideoWriter:
        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        return cv2.VideoWriter(path, fourcc, frames_per_sec, (width, height))

    def close_clips():
        # Release both writers and show the "Files saved" screen
        nonlocal writer_left, writer_right, saved_until
        if writer_left is None and writer_right is None:
            return
        if writer_left is not None:
            writer_left.release()
            writer_left = None
        if writer_right is not None:
            writer_right.release()
            writer_right = None
        short = timestamp[5:]  # drop the year so it fits in 20 chars
        lcd(["Files saved", f"L:{short}", f"R:{short}"])
        saved_until = time.monotonic() + SAVED_MESSAGE_SEC

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

                # Live status while recording (text only changes once per second)
                elapsed = frames_written // frames_per_sec
                lcd([
                    "Switch: ON",
                    "Recording...",
                    f"Time: {elapsed}s/{duration_sec}s",
                ])

                if frames_written >= total_frames:
                    close_clips()
            else:
                close_clips()
                # Show idle status once the "Files saved" message has been up long enough
                if time.monotonic() >= saved_until:
                    lcd(["Switch: OFF", "Not recording"])

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
        close_clips()  # leaves "Files saved" on the LCD at shutdown
        picam_left.stop()
        picam_right.stop()

if __name__ == "__main__":
    record_picam_left_right()