import cv2
import csv
import os
import numpy as np
from pathlib import Path
from datetime import datetime
from variables import DEBUG_PRINT






def get_time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def check_button(button_name) -> bool:
    """read the button port and tell the pi. On = True, Off = False"""

    # TODO
    return True


def tamprint(string: str):
    """print with a custom start"""
    print(f"TAM: {string}")


def debugprint(string: str):
    """print to terminal or not, depending on DEBUG_PRINT var"""
    if DEBUG_PRINT:
        tamprint(string=string)


def show_frame(frame: np.ndarray, window_name : str = "Frame"):
    '''wrapper for the 3 line cv2.imshow process'''

    
    cv2.imshow(winname= window_name, mat= frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


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


def draw_notched_rectangle(
    image : np.ndarray,
    center_x : int,
    top_y : int,
    width : int,
    height : int,
    base_length : int,
    angle_deg : int,
    color=(255, 255, 255),
    rotation_deg=0.0,
    border_thickness=1,
) -> np.ndarray:
    """
    Draw a filled, rotated rectangle with a V-notch and black border.

    Parameters
    ----------
    image : np.ndarray
        Destination image; modified in place.
    center_x, top_y : float
        Horizontal center and top edge BEFORE rotation, in pixels.
    width, height : float
        Rectangle dimensions before rotation, in pixels.
    base_length : float
        Width of the triangular opening along the unrotated top edge.
    angle_deg : float
        Interior angle at the bottom tip of the V, in degrees.
    color : tuple or int
        OpenCV BGR fill color, or a scalar for a grayscale image.
    rotation_deg : float
        Rotation about the rectangle's center, in degrees.
        Positive = counterclockwise as viewed on the image.
    border_thickness : int
        Black border width in pixels; must be at least 1.

    Returns
    -------
    np.ndarray
        The modified input image.
    """
    values = (
        center_x, top_y, width, height,
        base_length, angle_deg, rotation_deg,
    )
    if not all(np.isfinite(v) for v in values):
        raise ValueError("All geometry parameters must be finite.")
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive.")
    if not 0 < base_length < width:
        raise ValueError("base_length must be between 0 and width.")
    if not 0 < angle_deg < 180:
        raise ValueError("angle_deg must be between 0 and 180.")
    if (
        not isinstance(border_thickness, (int, np.integer))
        or border_thickness < 1
    ):
        raise ValueError("border_thickness must be a positive integer.")

    notch_depth = (base_length / 2) / np.tan(
        np.deg2rad(angle_deg / 2)
    )
    if notch_depth >= height:
        raise ValueError("The notch must be shallower than the rectangle.")

    left = center_x - width / 2
    right = center_x + width / 2
    bottom = top_y + height

    vertices = np.array([
        [left,                       top_y],
        [center_x - base_length / 2,  top_y],
        [center_x,                   top_y + notch_depth],
        [center_x + base_length / 2,  top_y],
        [right,                      top_y],
        [right,                      bottom],
        [left,                       bottom],
    ], dtype=np.float64)

    pivot = (float(center_x), float(top_y + height / 2))
    matrix = cv2.getRotationMatrix2D(
        pivot, float(rotation_deg), 1.0
    )
    rotated_vertices = vertices @ matrix[:, :2].T + matrix[:, 2]

    # Retain subpixel geometry until rasterization.
    shift = 8
    points = np.rint(
        rotated_vertices * (1 << shift)
    ).astype(np.int32)

    cv2.fillPoly(
        image,
        [points],
        color=color,
        lineType=cv2.LINE_AA,
        shift=shift,
    )

    black = 0 if image.ndim == 2 else (0,) * image.shape[2]

    cv2.polylines(
        image,
        [points],
        isClosed=True,
        color=black,
        thickness=int(border_thickness),
        lineType=cv2.LINE_AA,
        shift=shift,
    )

    return image



