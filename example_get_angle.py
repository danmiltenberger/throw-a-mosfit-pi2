import cv2
import numpy as np
from tam_frame import concat_frames, show_frame, resize_frame, get_field_frame, load_video_as_list_of_frames, show_frame_in_loop
from tam_draw import draw_angle_lines_on_camera_frame, draw_detection_to_camera_frame, draw_robot_to_field, draw_detection_to_field
from tam_vision import get_detection_from_name, get_hsv_frame
from tam_constants import BALL_RED
from tam_hsv import load_search_dict_from_csv
from tam_classes import Detection
from tam_topdown import try_to_merge_detections

def main():

    # yea I know these are mislabeled, but I think they were just saved the wrong way  
    right_cam_vid = "training_data/1280_720_RIGHT_2026_11_5_13_28.mp4"
    left_cam_vid = "training_data/1280_720_LEFT_2026_11_5_13_28.mp4"

    search_dict = load_search_dict_from_csv()
    frame_field = get_field_frame(left_is_green= True)
    frame_field_original = draw_robot_to_field(frame_field)

    frame_list_left = load_video_as_list_of_frames(left_cam_vid)
    frame_list_right = load_video_as_list_of_frames(right_cam_vid)

    min_list_frames = min(len(frame_list_left), len(frame_list_right))

    for i in range(min_list_frames):

        # get the frames from this iteration
        frame_field = frame_field_original.copy()
        frame_left = frame_list_left[i]
        frame_right = frame_list_right[i]

        # analyze for the ball
        frame_left, frame_field, ball_detect_left = process_frame_with_angle_lines(frame_left, frame_field, search_dict)
        frame_right, frame_field, ball_detect_right = process_frame_with_angle_lines(frame_right, frame_field, search_dict)

        # let's try to merge the detections to get the actual range
        ball_detect_merged = try_to_merge_detections(ball_detect_left, ball_detect_right)

        # draw either the left, right, or merged detection
        frame_field = draw_detection_to_field(frame_field, ball_detect_merged, draw_arrow=True, draw_lines=True)


        # package up to show
        frame = concat_frames(frame_left, frame_right, "DOWN")
        frame = concat_frames(frame, frame_field)
        frame = resize_frame(frame, 0.6)

        if show_frame_in_loop(frame) == False:
            break



def process_frame_with_angle_lines(frame_cam: np.ndarray, frame_field : np.ndarray, search_dict: dict) -> tuple[np.ndarray, np.ndarray, Detection]:
    frame_hsv = get_hsv_frame(frame_cam)
    ball_detection = get_detection_from_name(BALL_RED, frame_hsv, search_dict)

    frame_cam = draw_detection_to_camera_frame(frame_cam, ball_detection)
    frame_cam = draw_angle_lines_on_camera_frame(frame_cam)

    #frame_field = draw_detection_to_field(frame_field, ball_detection)

    return frame_cam, frame_field, ball_detection



if __name__ == "__main__":
    main()