from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_frame import overlap_frames, show_frame_in_loop, save_frame_as_png
from tam_draw import add_text_top
import numpy as np


def show_frames_and_wait_for_q():
    camL, camR = setup_left_right_cams()

    while True:
        left_frame, right_frame = get_left_right_frames(camL, camR)

        overlapped = overlap_frames(left_frame, right_frame)
        overlapped = add_text_top(overlapped, text="Hit q to take photo of all in one")
        if show_frame_in_loop(overlapped) == False:
            save_frame_as_png(left_frame, "hsv_photos/all_in_one_left.png")
            save_frame_as_png(right_frame, "hsv_photos/all_in_one_right.png")
            break


if __name__ == "__main__":
    show_frames_and_wait_for_q()






