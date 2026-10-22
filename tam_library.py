import cv2
import csv
import os
import numpy as np
from pathlib import Path
from datetime import datetime


def check_button(button_name) -> bool:
    """read the button port and tell the pi. On = True, Off = False"""

    # TODO
    return True


def show_frame(frame: np.ndarray, window_name : str = "Frame"):
    '''wrapper for the 3 line cv2.imshow process'''
    cv2.imshow(winname= window_name, mat= frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



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


def clear_csv(csv_file_path: str):
    """Remove all contents from a CSV file, creating it if it doesn't exist."""
    with open(csv_file_path, "w", newline="", encoding="utf-8"):
        pass


def append_dict_to_csv(csv_file_path: str, data: dict):
    """Append a dictionary as a CSV row, writing a header if the file is empty."""
    with open(csv_file_path, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(data.keys()))

        if os.fstat(csv_file.fileno()).st_size == 0:
            writer.writeheader()

        writer.writerow(data)
 

def timestamped_file_path(directory: str, ending: str) -> str:
    """Return a timestamped file path without creating the file or directory."""
    ending = ending.lstrip(".")
    timestamp = datetime.now().strftime("%Y_%m_%d_T_%H_%M_%S")
    filename = f"{timestamp}.{ending}" if ending else timestamp
    return str(Path(directory) / filename)


def load_dict_of_dicts_from_csv(
    csv_file_path: str,
    key_column: str,
) -> dict[str, dict[str, str]]:
    """Load CSV rows into nested dictionaries indexed by a unique column."""
    result = {}

    with open(csv_file_path, "r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            return result

        if key_column not in reader.fieldnames:
            raise ValueError(f"Column {key_column!r} not found in CSV.")

        for row in reader:
            key = row.pop(key_column)

            if key in result:
                raise ValueError(f"Duplicate key {key!r} in column {key_column!r}.")

            result[key] = row

    return result