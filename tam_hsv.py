import cv2
from pathlib import Path
import numpy as np
from tam_constants import *
from tam_frame import load_image_as_frame, show_frame
from tam_vision import get_hsv_frame, get_list_detections
from tam_draw import draw_detection_list_to_camera_frame

photos_and_vids_dir = TRAINING_DATA
hsv_dir = HSV_BOUNDS

import csv
import numpy as np


def main():

    csv_name = "classroom"

    file_path = "hsv_photos/all_in_one_right.png"

    # update_hsv(csv_name=csv_name, image_path= file_path, object_name= BALL_RED)
    # update_hsv(csv_name=csv_name, image_path= file_path, object_name= HAT_GREEN)
    # update_hsv(csv_name=csv_name, image_path= file_path, object_name= HAT_FUCHSIA)
    # update_hsv(csv_name=csv_name, image_path= file_path, object_name= HAT_YELLOW)
    # update_hsv(csv_name=csv_name, image_path= file_path, object_name= HAT_BLUE)

    # show what the program will detect

    frame = load_image_as_frame(file_path)
    frame_hsv = get_hsv_frame(frame.copy())

    search_dict = load_search_dict_from_csv()

    list_detections = get_list_detections(hsv_frame=frame_hsv, search_dict=search_dict)
    frame_annotated = draw_detection_list_to_camera_frame(frame, list_detections)
    show_frame(frame_annotated)




def update_hsv(object_name : str, image_path: str, csv_name: str):


    print(f"TUNE VALUES FOR {object_name}")
    file_path = HSV_BOUNDS + "/" + csv_name + ".csv"
    search_dict = load_search_dict_from_csv(filename=file_path)
    hsv_dict = tune_hsv_range(image_path=image_path, label= object_name)

    search_dict[object_name][HSV_HI] = hsv_dict[HSV_HI]
    search_dict[object_name][HSV_LO] = hsv_dict[HSV_LO]

    save_search_dict_to_csv(search_dict, file_path)
    print(f"saved {csv_name} to {HSV_BOUNDS}")




def save_search_dict_to_csv(search_dict, filename):
    """Save a nested search dictionary to a CSV file."""
    fieldnames = [
        "search_name",
        DRAW_COLOR,
        HSV_LO,
        HSV_HI,
        KNOWN_WIDTH,
        ANALYSIS_SHAPE,
        MIN_AREA_PX
    ]

    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for search_name, params in search_dict.items():
            row = {"search_name": search_name}

            for key, value in params.items():
                if isinstance(value, np.ndarray):
                    # Store arrays as comma-separated values: "169,213,67"
                    value = ",".join(str(int(x)) for x in value.tolist())

                row[key] = value

            writer.writerow(row)


def load_search_dict_from_csv(filename : str = HSV_CSV_PATH):
    """Load a CSV file back into the original nested dictionary format."""
    search_dict = {}

    with open(filename, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            search_name = row.pop("search_name")
            params = {}

            for key, value in row.items():
                if key in ("HSV_LO", "HSV_HI"):
                    if value and value != "to_be_determined":
                        params[key] = np.array(
                            [int(x) for x in value.split(",")],
                            dtype=np.uint8,
                        )
                    else:
                        params[key] = value
                elif key == "KNOWN_WIDTH":
                    params[key] = float(value)
                else:
                    params[key] = value

            search_dict[search_name] = params


    print(f"loaded search_dict from {filename}")
    return search_dict


def tune_hsv_range(image_path, label: str = ""):
    """
    Open an image, let the user click an object, tune an HSV mask,
    and save the accepted HSV range to a text file.

    Returns:
        tuple: (lower_hsv, upper_hsv, output_txt)
    """

    image_path = Path(image_path)
    frame = cv2.imread(str(image_path))

    if frame is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    height, width = frame.shape[:2]

    clicked_hsv = None

    def on_mouse_click(event, x, y, flags, param):
        nonlocal clicked_hsv

        if event == cv2.EVENT_LBUTTONDOWN:
            if 0 <= x < width and 0 <= y < height:
                clicked_hsv = hsv[y, x].copy()
                h, s, v = clicked_hsv
                print(f"\nClicked pixel HSV: H={h}, S={s}, V={v}")

    if label == "":
        window_name = "Click an object"
    else:
        window_name = f"Click on {label}"
    mask_window_name = "HSV Mask"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, on_mouse_click)

    # Initial range margins: H, S, V
    margins = np.array([10, 40, 40], dtype=np.int32)

    print("\nClick on the object you want to select.")
    print("After selecting it, use the terminal controls to adjust the mask.")

    while True:
        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1) & 0xFF

        if clicked_hsv is not None:
            break

        if key == 27:  # ESC
            cv2.destroyAllWindows()
            raise ValueError("No object was selected.")

    center = clicked_hsv.astype(np.int32)

    def make_bounds(center, margins):
        lower = np.maximum(center - margins, np.array([0, 0, 0]))
        upper = np.minimum(center + margins, np.array([179, 255, 255]))
        return lower, upper

    def create_mask(hsv_image, lower, upper):
        lower, upper = make_bounds(center, margins)

        lower_h = int(lower[0])
        upper_h = int(upper[0])

        # Handle hue wraparound, especially for red.
        if lower_h < 0 or upper_h > 179:
            lower = lower.copy()
            upper = upper.copy()

            # Example: center H=5, margin H=15 -> lower H=-10
            if lower_h < 0:
                lower[0] = 0
                upper[0] = 179

                low_mask = cv2.inRange(
                    hsv_image,
                    lower,
                    upper
                )

                wrapped_lower = np.array(
                    [180 + lower_h, lower[1], lower[2]],
                    dtype=np.uint8
                )
                wrapped_upper = np.array([179, upper[1], upper[2]], dtype=np.uint8)

                high_mask = cv2.inRange(hsv_image, wrapped_lower, wrapped_upper)
                return cv2.bitwise_or(low_mask, high_mask)

            # Example: center H=175, margin H=15 -> upper H=190
            if upper_h > 179:
                lower[0] = 0
                upper[0] = 179

                high_mask = cv2.inRange(
                    hsv_image,
                    lower,
                    upper
                )

                wrapped_lower = np.array([0, lower[1], lower[2]], dtype=np.uint8)
                wrapped_upper = np.array(
                    [upper_h - 180, upper[1], upper[2]],
                    dtype=np.uint8
                )

                low_mask = cv2.inRange(hsv_image, wrapped_lower, wrapped_upper)
                return cv2.bitwise_or(high_mask, low_mask)

        lower_uint8 = lower.astype(np.uint8)
        upper_uint8 = upper.astype(np.uint8)
        return cv2.inRange(hsv_image, lower_uint8, upper_uint8)

    mask = create_mask(hsv, center, margins)

    print("\nMask adjustment controls:")
    print("  w / s : increase / decrease H range")
    print("  a / d : increase / decrease S range")
    print("  q / e : increase / decrease V range")
    print("  SPACE : accept mask and save HSV range")
    print("  ESC   : cancel")

    while True:
        display = frame.copy()

        # Highlight accepted mask pixels in green on the original image.
        highlighted = display.copy()
        highlighted[mask == 255] = (0, 255, 0)
        display = cv2.addWeighted(display, 0.7, highlighted, 0.3, 0)

        lower, upper = make_bounds(center, margins)
        text = f"H:{lower[0]}-{upper[0]}  S:{lower[1]}-{upper[1]}  V:{lower[2]}-{upper[2]}"
        cv2.putText(
            display,
            text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            3,
            cv2.LINE_AA
        )
        cv2.putText(
            display,
            text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        cv2.imshow(window_name, display)
        cv2.imshow(mask_window_name, mask)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("w"):
            margins[0] += 1
        elif key == ord("s"):
            margins[0] = max(0, margins[0] - 1)
        elif key == ord("a"):
            margins[1] += 1
        elif key == ord("d"):
            margins[1] = max(0, margins[1] - 1)
        elif key == ord("q"):
            margins[2] += 1
        elif key == ord("e"):
            margins[2] = max(0, margins[2] - 1)
        elif key == ord(" "):
            break
        elif key == 27:
            cv2.destroyAllWindows()
            raise ValueError("HSV range tuning cancelled.")

        mask = create_mask(hsv, center, margins)

    lower, upper = make_bounds(center, margins)
    lower = lower.astype(np.uint8)
    upper = upper.astype(np.uint8)



    print(f"\nAccepted HSV range returned")
    print(f"HSV_HI: np.array({upper.tolist()})")
    print(f"HSV_LO: np.array({lower.tolist()})")

    cv2.destroyAllWindows()

    return_dict = {
        HSV_LO : lower,
        HSV_HI : upper
    }

    return return_dict



if __name__ == "__main__":
    main()