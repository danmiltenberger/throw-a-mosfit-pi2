import os
from datetime import datetime
from tam_constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y, CAMERA_CAPTURE_FPS

import cv2
from picamera2 import Picamera2 #type: ignore




WINDOW_NAME = "Pi Camera"
RECORD_KEY = 32      # Space
PHOTO_KEY = ord("s")
QUIT_KEY = ord("q")


def create_camera():
    """Create and start a Picamera2 camera configured for OpenCV BGR frames."""
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"size": (CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y), "format": "RGB888"},
        controls={"FrameRate": CAMERA_CAPTURE_FPS},
    )
    picam2.configure(config)
    picam2.start()
    return picam2


def get_frame(picam2):
    """Return the current camera frame as a clean 3-channel BGR NumPy array."""
    frame = picam2.capture_array("main")

    if frame.ndim == 3 and frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    else:
        # Picamera2's RGB888/BGR888 naming is counterintuitive:
        # the captured NumPy array is RGB, while OpenCV uses BGR.
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    return frame


def default_filename(extension):
    """Return an ISO-like timestamped filename, e.g. 2026_10_31_T_17_06_00.png."""
    timestamp = datetime.now().strftime("%Y_%m_%d_T_%H_%M_%S")
    return f"{timestamp}.{extension}"


def prompt_for_filename(extension):
    """Ask for a filename in the terminal; use a timestamp if blank."""
    name = input(f"Enter filename (without .{extension}, blank for timestamp): ").strip()

    if not name:
        name = default_filename(extension)

    if not name.lower().endswith(f".{extension}"):
        name += f".{extension}"

    name = "training_data/" + name
    return name


def save_photo(frame):
    """Prompt for a filename and save the clean frame as a PNG."""
    filename = prompt_for_filename("png")
    cv2.imwrite(filename, frame)
    print(f"Saved photo: {filename}")


def start_recording(frame, fps):
    """Create an OpenCV VideoWriter using the frame's dimensions."""
    filename = prompt_for_filename("mp4")
    height, width = frame.shape[:2]
    writer = cv2.VideoWriter(
        filename,
        cv2.VideoWriter.fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer for {filename}")

    print(f"Recording: {filename}")
    return writer, filename


def stop_recording(writer, filename):
    """Release the writer and report the saved video."""
    writer.release()
    print(f"Saved video: {filename}")


def draw_overlay(frame, recording, recording_started_at):
    """Return a display-only copy with instructions and recording duration."""
    display = frame.copy()

    if recording:
        elapsed = max(0.0, cv2.getTickCount() / cv2.getTickFrequency() - recording_started_at)
        status = f"RECORDING  {elapsed:.1f}s"
        color = (0, 0, 255)
    else:
        status = "READY"
        color = (0, 255, 0)

    lines = [
        "SPACE: start/stop recording",
        "S: save photo",
        "Q: quit",
        status,
    ]

    y = 30
    for line in lines:
        cv2.putText(
            display,
            line,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )
        y += 28

    return display


def run_camera():
    """Main camera loop: preview, record, photograph, and quit."""
    picam2 = create_camera()

    writer = None
    output_filename = None
    recording_started_at = None

    try:
        while True:
            frame = get_frame(picam2)

            recording = writer is not None
            display = draw_overlay(frame, recording, recording_started_at)

            cv2.imshow(WINDOW_NAME, display)
            key = cv2.waitKey(1) & 0xFF

            if key == QUIT_KEY:
                break

            elif key == RECORD_KEY:
                if writer is None:
                    writer, output_filename = start_recording(frame, CAMERA_CAPTURE_FPS)
                    recording_started_at = cv2.getTickCount() / cv2.getTickFrequency()
                else:
                    stop_recording(writer, output_filename)
                    writer = None
                    output_filename = None
                    recording_started_at = None

            elif key == PHOTO_KEY:
                save_photo(frame)

            if writer is not None:
                writer.write(frame)

    finally:
        if writer is not None:
            writer.release()

        cv2.destroyAllWindows()
        picam2.stop()


if __name__ == "__main__":
    run_camera()