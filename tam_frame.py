import numpy as np
import cv2
from datetime import datetime
from pathlib import Path


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


def get_field_frame(USE_DRAWN_FIELD : bool = True) -> np.ndarray:

    if USE_DRAWN_FIELD:
        frame = load_image_as_frame("field_pngs/field_empty.png")
    else:
        frame = load_image_as_frame("field_pngs/field_black.png")

    return frame


def show_frame(frame: np.ndarray, window_name : str = "Frame"):
    '''wrapper for the 3 line cv2.imshow process'''

    
    cv2.imshow(winname= window_name, mat= frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def show_frame_in_loop(
    frame: np.ndarray,
    window_name: str = "Frame",
    delay_ms: int = 1,
    quit_keys: tuple[str, ...] = ("q", "Q"),
) -> bool:
    """
    Display a frame from within a while loop.

    Returns:
        bool: False if the user requested to quit, otherwise True.

    Quit conditions:
        - Press Esc
        - Press any key listed in quit_keys (default: q or Q)
        - Close the display window
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(
            f"frame must be numpy.ndarray, got {type(frame).__name__}"
        )

    if not isinstance(window_name, str):
        raise TypeError(
            f"window_name must be a string, got {type(window_name).__name__}"
        )

    if not isinstance(delay_ms, int) or delay_ms < 1:
        raise ValueError(
            f"delay_ms must be a positive integer, got {delay_ms}"
        )

    cv2.imshow(winname=window_name, mat=frame)

    key = cv2.waitKey(delay_ms) & 0xFF

    # Esc key
    if key == 27:
        cv2.destroyWindow(window_name)
        return False

    # Configurable quit keys
    if any(key == ord(quit_key) for quit_key in quit_keys):
        cv2.destroyWindow(window_name)
        return False

    # Window was closed with the X button.
    # This check is best-effort because behavior varies by OS/backend.
    try:
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            cv2.destroyWindow(window_name)
            return False
    except cv2.error:
        cv2.destroyWindow(window_name)
        return False

    return True


def load_image_as_frame(im_path: str) -> np.ndarray:
    """Load an image as a three-channel BGR frame.

    Raises:
        TypeError: If im_path is not a string.
        ValueError: If im_path is blank or the image cannot be decoded.
        FileNotFoundError: If the path does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    if not isinstance(im_path, str):
        raise TypeError(
            f"im_path must be a str, got {type(im_path).__name__}"
        )

    if not im_path.strip():
        raise ValueError("im_path must not be empty or whitespace-only.")

    path = Path(im_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    if path.is_dir():
        raise IsADirectoryError(f"Expected an image file, got a directory: {path}")

    frame = cv2.imread(str(path), cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError(f"Unable to read or decode image: {path}")

    if not isinstance(frame, np.ndarray):
        raise TypeError(
            f"Expected np.ndarray, got {type(frame).__name__}"
        )

    return frame


def save_frame_as_png(frame : np.ndarray, file_name : str = ""):

    if file_name == "":
        file_name = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")

    file_name = "training_data/" + file_name + ".png"
    cv2.imwrite(file_name, img= frame)
    print(f"saved {file_name}")


def load_video_as_list_of_frames(vid_path: str) -> list[np.ndarray]:
    """Load a local video into a list of BGR uint8 frames.

    Args:
        vid_path: Path to a local video file.

    Returns:
        A nonempty list of arrays with shape (height, width, 3).
        All frames have the same shape and dtype np.uint8.

    Raises:
        TypeError: If vid_path is not a string.
        ValueError: If vid_path is blank, the file is empty, or no frames
            can be decoded.
        FileNotFoundError: If the path does not exist.
        IsADirectoryError: If the path points to a directory.
        OSError: If the path is not a regular file, or OpenCV cannot open
            or decode the video.
        RuntimeError: If a decoded frame violates the output contract.

    Note:
        Loads the entire decoded video into memory.
        A failed read after valid frames is treated as end-of-stream;
        this does not guarantee that the source video is uncorrupted.
    """

    print(f"beginning loading video as frames: {vid_path}")

    if not isinstance(vid_path, str):
        raise TypeError(
            f"vid_path must be a str, got {type(vid_path).__name__}."
        )
    if not vid_path.strip():
        raise ValueError("vid_path must not be empty or whitespace-only.")

    path = Path(vid_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Video file does not exist: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Expected a video file, got a directory: {path}")
    if not path.is_file():
        raise OSError(f"Path is not a regular file: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Video file is empty: {path}")

    frames: list[np.ndarray] = []
    expected_shape: tuple[int, ...] | None = None
    capture = cv2.VideoCapture()

    try:
        if not capture.open(str(path)) or not capture.isOpened():
            raise OSError(f"OpenCV could not open video: {path}")

        while True:
            success, frame = capture.read()
            if not success:
                break

            index = len(frames)

            if not isinstance(frame, np.ndarray):
                raise RuntimeError(
                    f"Frame {index}: expected np.ndarray, "
                    f"got {type(frame).__name__}."
                )
            if frame.size == 0:
                raise RuntimeError(f"Frame {index}: decoded frame is empty.")
            if frame.ndim != 3 or frame.shape[2] != 3:
                raise RuntimeError(
                    f"Frame {index}: expected shape (H, W, 3), "
                    f"got {frame.shape}."
                )
            if frame.dtype != np.uint8:
                raise RuntimeError(
                    f"Frame {index}: expected uint8, got {frame.dtype}."
                )

            if expected_shape is None:
                expected_shape = frame.shape
            elif frame.shape != expected_shape:
                raise RuntimeError(
                    f"Frame {index}: expected shape {expected_shape}, "
                    f"got {frame.shape}."
                )

            frames.append(frame)

    except cv2.error as exc:
        raise OSError(f"OpenCV failed while decoding video: {path}") from exc
    finally:
        capture.release()

    if not frames:
        raise ValueError(f"Video contains no decodable frames: {path}")

    return frames

