
import cv2
import numpy as np
from time import sleep
from tam_classes import FieldState, Detection
from tam_frame import get_field_frame, load_image_as_frame, show_frame, load_video_as_list_of_frames, concat_frames, rotate_image
from tam_hsv import load_search_dict_from_csv
from tam_vision import example_vision_full_stack, get_fieldstate_from_frame, get_annotated_frame, get_hsv_frame, get_list_detections
from tam_draw import draw_fieldstate, draw_detection_list_to_camera_frame, draw_robot_to_field, draw_arrow_point_to_point, inches_to_screen, draw_line_point_to_point
from tam_decide import convert_detect_list_to_fieldstate, get_init_fieldstate, convert_detect_list_to_dict
from tam_topdown import convert_to_field
from tam_constants import BALL_RED, MIN_AREA_PX, HAT_FUCHSIA, HAT_GREEN, BEARING_NORTH
from tam_points import FIELD_CENTER, FIELD_GOALBOX_CENTER_BOTTOM
from tam_colors import BLUE, YELLOW, GREEN, PURPLE, WHITE


def main():
    vid_path = "training_data/2026_11_02_T_15_36_33.mp4"
    goalposts_video(vid_path)


    





def goalposts_video(video_path: str, frames_per_sec = 1):
    original_frame_field = get_field_frame(left_is_green=True)
    search_dict = load_search_dict_from_csv()

    sec_per_frame = 1/frames_per_sec

    list_frames_camera = load_video_as_list_of_frames(video_path)

    prev_state = get_init_fieldstate()

    for frame in list_frames_camera:

        side_by_side = testing_goalposts_from_frame(frame, original_frame_field.copy(), search_dict)

        cv2.imshow("Side by side", side_by_side)

        sleep(sec_per_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


def testing_goalposts_from_frame(frame_camera: np.ndarray, frame_field: np.ndarray, search_dict: dict) -> np.ndarray:
    '''if given an image with both goalposts, can we figure out our bot's position?'''


    # looking for goalpost
    hsv_frame = get_hsv_frame(frame_camera)
    detect_list = get_list_detections(hsv_frame, search_dict)

    detect_dict = convert_detect_list_to_dict(detect_list)

    detection_gp_green : Detection = detect_dict[HAT_GREEN]
    detection_gp_purple : Detection = detect_dict[HAT_FUCHSIA]

    detect_list_gp = [detection_gp_green, detection_gp_purple]


    # lets first just draw arrows from a centered robot to where we think the goals are
    our_bot_pos_in = FIELD_GOALBOX_CENTER_BOTTOM
    green_gp_pos_in = convert_to_field(
        our_bot_pos_in,
        BEARING_NORTH,
        object_dis= detection_gp_green.dis_from_bot_in,
        object_bearing_rad= detection_gp_green.ang_from_bot_rad
    )

    purple_gp_pos_in = convert_to_field(
        our_bot_pos_in,
        BEARING_NORTH,
        object_dis= detection_gp_purple.dis_from_bot_in,
        object_bearing_rad= detection_gp_purple.ang_from_bot_rad
    )

    frame_field = draw_robot_to_field(
        field_frame= frame_field,
        bearing_rad= BEARING_NORTH,
        color= YELLOW,
        pos_in= our_bot_pos_in
    )

    # draw an arrow from bot to green goalpost
    frame_field = draw_arrow_point_to_point(
        frame= frame_field,
        start= inches_to_screen(our_bot_pos_in),
        end= inches_to_screen(green_gp_pos_in),
        color= GREEN
    )

    # draw an arrow from bot to purple goalpost
    frame_field = draw_arrow_point_to_point(
        frame= frame_field,
        start= inches_to_screen(our_bot_pos_in),
        end= inches_to_screen(purple_gp_pos_in),
        color= PURPLE
    )

    # draw a line from goalpost to goalpost (simulating the goal)
    frame_field = draw_line_point_to_point(
        frame= frame_field,
        color= WHITE,
        end= inches_to_screen(purple_gp_pos_in),
        start= inches_to_screen(green_gp_pos_in)
    )

    # draw info to the camera
    frame_camera = draw_detection_list_to_camera_frame(frame_camera, detect_list_gp)
    frame_camera = draw_line_point_to_point(
        frame= frame_camera,
        color= WHITE,
        start= detection_gp_green.camera_pos_px,
        end= detection_gp_purple.camera_pos_px
    )


    side_by_side = concat_frames(frame_camera, frame_field)

    return side_by_side


def vision_and_decision_from_photo(photo_path: str):

    frame_camera = load_image_as_frame(photo_path)
    frame_field = get_field_frame(left_is_green= True)

    search_dict = load_search_dict_from_csv()
    hsv_frame = get_hsv_frame(frame_camera)

    detect_list = get_list_detections(hsv_frame, search_dict)

    fieldstate = convert_detect_list_to_fieldstate(detect_list)

    frame_camera = draw_detection_list_to_camera_frame(frame_camera, detect_list)
    frame_field = draw_fieldstate(frame_field, fieldstate)


    side_by_side = concat_frames(frame_camera, frame_field)

    show_frame(side_by_side)


def vision_and_decision_from_vid(vid_path: str, frames_per_sec = 10):
    original_frame_field = get_field_frame()
    search_dict = load_search_dict_from_csv()

    sec_per_frame = 1/frames_per_sec

    list_frames_camera = load_video_as_list_of_frames(vid_path)

    prev_state = get_init_fieldstate()

    for frame_camera in list_frames_camera:

        frame_field = original_frame_field.copy()

        hsv_frame = get_hsv_frame(frame_camera)
       
        detect_list = get_list_detections(hsv_frame, search_dict)

        fieldstate = convert_detect_list_to_fieldstate(detect_list, prev_state)

        frame_camera = draw_detection_list_to_camera_frame(frame_camera, detect_list)

        frame_field = draw_fieldstate(frame_field, fieldstate)

        side_by_side = concat_frames(frame_camera, frame_field)

        fieldstate = prev_state

        cv2.imshow("Side by side", side_by_side)

        sleep(sec_per_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


def vision_full_stack_one_frame():
    frame_camera = load_image_as_frame("training_data/red_ball_centerframe.png")
    frame_field = get_field_frame(USE_DRAWN_FIELD= False)

    search_dict = load_search_dict_from_csv()

    frame_full = example_vision_full_stack(frame_field= frame_field, frame_camera=frame_camera, search_dict= search_dict)

    show_frame(frame_full)


if __name__ == "__main__":

    main()