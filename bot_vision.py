import numpy as np
import cv2

# from picamera2 import Picamera2 #type: ignore
from constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y
from tam_library_analyze_camera import (
    get_detected_object,
    get_hsv_frame,
    get_mask_frame,
    show_frame,
    get_contours_from_mask,
    draw_contours,
    get_object_info_from_contours,
    draw_object_to_frame
)
from tam_library_analyze_field import concat_frames
from tam_library_draw_field import get_field_frame, draw_robot_to_field, draw_ball_to_field, draw_top_down_arrows
from tam_library_front_and_top_down import calc_angle_from_screen_center, calc_distance_from_bot, convert_to_field
from tam_library import load_image_as_frame, add_text_top, load_video_as_list_of_frames, show_frame_in_loop
from tam_library_lcd import lcd_fieldstate
from constants import search_dict, BALL_RED, HSV_LO, HSV_HI, YELLOW, KNOWN_WIDTH
from constants_points import FIELD_GOALBOX_CENTER_BOTTOM
from constants_rads import BEARING_NORTH
from classes import Point


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


def vision_full_stack(frame_camera : np.ndarray, frame_field: np.ndarray) -> np.ndarray:
    robot_pos = FIELD_GOALBOX_CENTER_BOTTOM
    robot_rad = BEARING_NORTH
    robot_color = YELLOW


    # put our bot at our goalbox
    frame_field = add_text_top(frame_field, "FIELD")
    frame_field = draw_robot_to_field(
        field_frame= frame_field,
        bearing_rad= robot_rad,
        pos_in= robot_pos,
        color= robot_color
    )


    frame_hsv = get_hsv_frame(frame_camera.copy())

    # load the hsv bounds and filter
    hsv_lo = search_dict[BALL_RED][HSV_LO]
    hsv_hi = search_dict[BALL_RED][HSV_HI]
    frame_mask = get_mask_frame(frame_hsv.copy(), hsv_hi=hsv_hi, hsv_lo=hsv_lo)

    # determine the contours
    contours, _ = get_contours_from_mask(frame_mask=frame_mask)
    frame_contours = draw_contours(frame_camera.copy(), contours)
    frame_contours = add_text_top(frame_contours, "CONTOURS")
    object_info = get_object_info_from_contours(contours, analyze_as_circle= True)
    frame_annotated = draw_object_to_frame(frame_camera.copy(), object_info)
    frame_annotated = add_text_top(frame_annotated, "BEST CONTOUR")

    # if it find's the ball, calculate and draw it
    if object_info["WIDTH_PX"] > 0:

        # determine the range and angle to the ball
        known_width_in = search_dict[BALL_RED][KNOWN_WIDTH]
        dis_from_bot_in = calc_distance_from_bot(known_width_in=known_width_in, percieved_width_px= object_info["WIDTH_PX"])

        center_on_screen = Point(object_info["CENTER_X_PX"], object_info["CENTER_Y_PX"])
        ang_from_bot_rad = calc_angle_from_screen_center(point=center_on_screen)

        ball_pos_in : Point = convert_to_field(
            object_bearing_rad= ang_from_bot_rad,
            object_dis= dis_from_bot_in,
            robot_bearing_rad= robot_rad,
            robot_pos= robot_pos
        )

        # add the ball to the field
        frame_field = draw_ball_to_field(frame_field, ball_pos_in)

        # draw arrows explaining
        frame_field = draw_top_down_arrows(
            field_frame= frame_field,
            ref_bearing_rad= robot_rad,
            ref_point_in= robot_pos,
            target_point_in= ball_pos_in,
        )


    ### Show User
    # combine frames together to more easily compare
    # frame mask is black and white but concat_frames needs color
    frame_mask = cv2.cvtColor(frame_mask, cv2.COLOR_GRAY2BGR)
    frame_mask = add_text_top(frame_mask, "MASK")
    frame_camera = add_text_top(frame_camera, "ORIGINAL")


    # top row
    top_row = concat_frames(frame_camera, frame_mask)

    # bottom row
    bottom_row = concat_frames(frame_annotated, frame_contours)

    # combine
    four_by_four = concat_frames(top_row, bottom_row, "DOWN")

    combined_frame = concat_frames(four_by_four, frame_field)

    return combined_frame


# Example usage
if __name__ == "__main__":


    frame_camera = load_image_as_frame("training_data/red_ball_centerframe.png")
    frame_field = get_field_frame(USE_DRAWN_FIELD= False)
    frame_full = vision_full_stack(frame_field= frame_field, frame_camera=frame_camera)

    #show_frame(frame_full)


    list_frames_camera = load_video_as_list_of_frames("training_data/red_ball_vid.h264")


    for frame_camera in list_frames_camera:
        frame_full = vision_full_stack(frame_field= frame_field, frame_camera=frame_camera)

        if not show_frame_in_loop(frame_full, window_name="Frame", delay_ms=1):
            break

        




    # # Create once at program startup
    # picam2 = Picamera2()

    # # RGB888 gives an OpenCV-compatible 3-channel image
    # config = picam2.create_video_configuration(
    #     main={"format": "RGB888", "size": (CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y)}
    # )
    # picam2.configure(config)
    # picam2.start()
    # try:
    #     while True:
    #         frame = get_frame(picam2)

    #         # Your OpenCV processing here
    #         cv2.imshow("Raspberry Pi Camera", frame)

    #         if cv2.waitKey(1) & 0xFF == ord("q"):
    #             break
    # finally:
    #     picam2.stop()
    #     cv2.destroyAllWindows()
