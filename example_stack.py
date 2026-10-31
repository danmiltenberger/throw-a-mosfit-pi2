import numpy as np
import cv2

# from picamera2 import Picamera2 #type: ignore
from tam_classes import Point
from tam_constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y
from tam_frame import load_image_as_frame, load_video_as_list_of_frames
from tam_points import FIELD_GOALBOX_CENTER_BOTTOM
from tam_constants import *
from tam_draw import add_text_top, draw_robot_to_field, draw_ball_to_field, draw_top_down_arrows
from tam_vision import get_hsv_frame, get_mask_frame, get_contours, get_object_info_from_contours
from tam_topdown import calc_distance_from_bot, calc_angle_from_screen_center, convert_to_field



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
    contours, _ = get_contours(frame_mask=frame_mask)
    object_info = get_object_info_from_contours(contours, analyze_as_circle= True)

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

    left_col = concat_frames(frame_camera, frame_mask, "DOWN")

    combined_frame = concat_frames(left_col, frame_field, "RIGHT")

    return combined_frame


# Example usage
if __name__ == "__main__":


    frame_camera = load_image_as_frame("training_data/red_ball_centerframe.png")
    frame_field = get_field_frame(USE_DRAWN_FIELD= False)
    frame_full = vision_full_stack(frame_field= frame_field, frame_camera=frame_camera)

    #show_frame(frame_full)


    list_frames_camera = load_video_as_list_of_frames("training_data/red_ball_vid.h264")


    for frame_camera in list_frames_camera:
        frame_full = vision_full_stack(frame_field= frame_field.copy(), frame_camera=frame_camera)

        cv2.imshow("Vision Stack", frame_full)

        if cv2.waitKey(1) & 0xFF == ord("q"):
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
