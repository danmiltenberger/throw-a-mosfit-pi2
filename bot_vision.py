import numpy as np
import cv2
from picamera2 import Picamera2 #type: ignore
from constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y

# Create once at program startup
picam2 = Picamera2()

# RGB888 gives an OpenCV-compatible 3-channel image
config = picam2.create_video_configuration(
    main={"format": "RGB888", "size": (CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y)}
)
picam2.configure(config)
picam2.start()


def get_frame() -> np.ndarray:
    """
    Capture one frame from the Raspberry Pi camera.

    Returns:
        np.ndarray: BGR image with shape (height, width, 3), dtype uint8.
    """
    frame = picam2.capture_array("main")  # RGB ndarray

    if frame is None:
        raise RuntimeError("Failed to capture frame from Picamera2.")

    # OpenCV generally expects BGR order
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


# Example usage
if __name__ == "__main__":
    try:
        while True:
            frame = get_frame()

            # Your OpenCV processing here
            cv2.imshow("Raspberry Pi Camera", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        picam2.stop()
        cv2.destroyAllWindows()