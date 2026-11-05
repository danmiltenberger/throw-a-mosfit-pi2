import os
from datetime import datetime

import cv2
import numpy as np
from picamera2 import Picamera2


def record_two_picams(
    duration_s: float = 60.0,
    resolution: tuple[int, int] = (1280, 720),
    fps: int = 30,
    left_camera_id: int = 0,
    right_camera_id: int = 1,
    output_dir: str = "bino_vision",
    preview: bool = True,
) -> tuple[str, str]:
    """
    Record simultaneous video from two Picamera2 cameras using OpenCV.

    Returns:
        (left_mp4_path, right_mp4_path)
    """

    width, height = resolution
    os.makedirs(output_dir, exist_ok=True)

    # Example: 1280_720_LEFT_2026_11_5_13_04.mp4
    timestamp = datetime.now().strftime("%Y_%-m_%-d_%-H_%M")

    left_path = os.path.join(
        output_dir, f"{width}_{height}_LEFT__{timestamp}.mp4"
    )
    right_path = os.path.join(
        output_dir, f"{width}_{height}_RIGHT_{timestamp}.mp4"
    )

    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    left_writer = cv2.VideoWriter(left_path, fourcc, fps, (width, height))
    right_writer = cv2.VideoWriter(right_path, fourcc, fps, (width, height))

    if not left_writer.isOpened() or not right_writer.isOpened():
        left_writer.release()
        right_writer.release()
        raise RuntimeError("OpenCV could not open one or both MP4 writers.")

    # Configure both cameras.
    left_cam = Picamera2(left_camera_id)
    right_cam = Picamera2(right_camera_id)

    config = {
        "main": {
            "size": (width, height),
            "format": "RGB888",  # OpenCV expects BGR; convert below.
        },
        "controls": {"FrameRate": fps},
    }

    left_cam.configure(left_cam.create_video_configuration(**config))
    right_cam.configure(right_cam.create_video_configuration(**config))

    try:
        # Start both before recording so their startup delay is similar.
        left_cam.start()
        right_cam.start()

        frame_interval = 1.0 / fps
        frames_to_capture = int(duration_s * fps)

        for _ in range(frames_to_capture):
            left_frame = left_cam.capture_array("main")
            right_frame = right_cam.capture_array("main")

            # Picamera2 "RGB888" already provides BGR-ordered data for OpenCV.
            left_bgr = np.asarray(left_frame)
            right_bgr = np.asarray(right_frame)

            left_writer.write(left_bgr)
            right_writer.write(right_bgr)

            if preview:
                combined = np.hstack((left_bgr, right_bgr))
                cv2.imshow("LEFT | RIGHT", combined)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cv2.waitKey(int(frame_interval * 1000))

    finally:
        left_cam.stop()
        right_cam.stop()
        left_writer.release()
        right_writer.release()
        if preview:
            cv2.destroyAllWindows()

    return left_path, right_path


if __name__ == "__main__":
    left_file, right_file = record_two_picams(
        duration_s=60,
        resolution=(1280, 720),
        fps=30,
        left_camera_id=0,
        right_camera_id=1,
        preview=True,
    )

    print(f"Saved: {left_file}")
    print(f"Saved: {right_file}")