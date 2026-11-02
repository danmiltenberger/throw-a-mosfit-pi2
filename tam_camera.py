import numpy as np

def get_frame(picam2) -> np.ndarray:
    """
    Capture one frame from the Raspberry Pi camera.

    Returns:
        np.ndarray: BGR image with shape (height, width, 3), dtype uint8.
    """
    frame = picam2.capture_array("main")  # RGB ndarray

    if frame is None:
        raise RuntimeError("Failed to capture frame from Picamera2.")

    # OpenCV generally expects BGR order
    # return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    # Turns out this isn't necessary!
    return frame