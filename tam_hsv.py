import cv2
from pathlib import Path
import numpy as np
from constants import *

photos_and_vids_dir = TRAINING_DATA
hsv_dir = HSV_BOUNDS



def tune_hsv_range(image_path, output_txt="hsv_range.txt"):
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

    window_name = "Click an object"
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

    with open(output_txt, "w") as f:
        f.write(f"lower_hsv = {lower.tolist()}\n")
        f.write(f"upper_hsv = {upper.tolist()}\n")


    # format
    # HSV_HI: np.array([0, 200, 0], dtype=np.uint8),
    # HSV_LO: np.array([10, 255, 157], dtype=np.uint8)

    print(f"\nAccepted HSV range saved to: {output_txt}")
    print(f"HSV_HI: np.array({upper.tolist()})")
    print(f"HSV_LO: np.array({lower.tolist()})")

    cv2.destroyAllWindows()

    return lower, upper, output_txt


def main():
    #frame = get_or_load_frame()

    #output_txt = hsv_dir + "/ball_red.txt"
    #output_txt = hsv_dir + "/hat_yellow.txt"
    #output_txt = hsv_dir + "/hat_cyan.txt"

    obj_name = BALL_RED
    given_png = "training_data/red_ball_centerframe.png"

    output_txt_file = hsv_dir + "/" + obj_name + ".txt"


    tune_hsv_range(given_png, output_txt_file)



if __name__ == "__main__":
    main()