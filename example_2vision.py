import cv2
import numpy as np
import math
from time import sleep
from tam_frame import load_video_as_list_of_frames, concat_frames, show_frame, load_image_as_frame, get_field_frame
from tam_vision import get_detection_from_name, get_hsv_frame
from tam_constants import BALL_RED
from tam_hsv import load_search_dict_from_csv
from tam_classes import Detection
from tam_topdown import get_dis_and_angle_deg_to_obj_from_two_cam, get_angle_of_object_deg_from_3oclock
from tam_draw import draw_detection_to_camera_frame, draw_detection_to_field_frame, add_text_top, draw_robot_to_field



def main():

    search_dict = load_search_dict_from_csv()


    frame_left = "training_data/vlcsnap-2026-11-06-14h52m20s060.png"
    frame_right = "training_data/vlcsnap-2026-11-06-14h53m08s753.png"

    frame_field = get_field_frame(left_is_green=True, USE_DRAWN_FIELD=False)

    frame_field = draw_robot_to_field(frame_field)

    frame_left = load_image_as_frame(frame_left)
    frame_right = load_image_as_frame(frame_right)

    frame = test_2vision_frame(frame_left, frame_right, frame_field, search_dict)



    show_frame(frame, scale=0.6)



def test_2vision_video(search_dict: dict):
    path_to_cam_vid_left = "training_data/1280_720_2026_11_5_13_28_LEFT.mp4"
    path_to_cam_vid_right = "training_data/1280_720_2026_11_5_13_28_RIGHT.mp4"


    width = 1280
    height = 720 + 720

    resize_mult = 0.6
    resized_x = int(width * resize_mult)
    resized_y = int(height * resize_mult)

    frames_per_sec = 60
    sec_per_frame = 1 / frames_per_sec

    print("loading video left")
    list_frames_left = load_video_as_list_of_frames(path_to_cam_vid_left)

    print("loading video right")
    list_frames_right = load_video_as_list_of_frames(path_to_cam_vid_right)

    len_list_left = len(list_frames_left)
    len_list_right = len(list_frames_right)

    len_min = min(len_list_left,len_list_right)


    for i in range(len_min):
        frame_left = list_frames_left[i]
        frame_right = list_frames_right[i]

        # left_right = test_2vision_frame(frame_left, frame_right, search_dict)

        # left_right = cv2.resize(left_right, (resized_x, resized_y))

        # cv2.imshow("left_right", left_right)
        
        # sleep(sec_per_frame)    

        # if cv2.waitKey(1) & 0xFF == ord("q"):
        #     break
    


def test_2vision_frame(frame_left: np.ndarray, frame_right : np.ndarray, frame_field: np.ndarray, search_dict: dict) -> np.ndarray:
    '''with two images, search for objects and determine positions from both'''

    hsv_frame_left = get_hsv_frame(frame_left.copy())
    hsv_frame_right = get_hsv_frame(frame_right.copy())

    ball_detection_left = get_detection_from_name(BALL_RED, hsv_frame_left, search_dict)
    ball_detection_right = get_detection_from_name(BALL_RED, hsv_frame_right, search_dict)

    frame_left = draw_detection_to_camera_frame(frame_left, ball_detection_left)
    frame_left = add_text_top(frame_left, "LEFT EYE")
    frame_right = draw_detection_to_camera_frame(frame_right, ball_detection_right)
    frame_right = add_text_top(frame_right, "RIGHT EYE")

    print(ball_detection_left)
    print(ball_detection_right)
    ball_detection_merged = merge_detections(ball_detection_left, ball_detection_right)
    print(ball_detection_merged)

    # draw the estimated distances
    frame_field = draw_detection_to_field_frame(frame_field, ball_detection_left, label= "Left Eye")
    frame_field = draw_detection_to_field_frame(frame_field, ball_detection_right, label="Right Eye")

    # draw the merged distance and angle
    frame_field = draw_detection_to_field_frame(frame_field, ball_detection_merged, label="Merged")
    frame_field = add_text_top(frame_field, "FIELD")

    frame = concat_frames(frame_left,frame_right, "DOWN")
    frame = concat_frames(frame, frame_field, "RIGHT")

    return frame


def merge_detections(detect_left: Detection, detect_right: Detection) -> Detection:
    '''try to merge two detections into one seen object'''

    # if both are in frame we can attempt to merge them
    if (detect_left.in_frame == True) and (detect_left.in_frame == True):

        # update the angles
        angle_left_deg = math.radians(get_angle_of_object_deg_from_3oclock(int(detect_left.camera_pos_px.x)))
        angle_right_deg = math.radians(get_angle_of_object_deg_from_3oclock(int(detect_right.camera_pos_px.x)))

        # get the distance from the angles
        dis_in, angle_deg = get_dis_and_angle_deg_to_obj_from_two_cam(angle_left_deg, angle_right_deg)

        print(f"merged detections! dis is {round(dis_in,1)}in, instead of {round(detect_left.dis_from_bot_in,1)} or {round(detect_right.dis_from_bot_in,1)}in")


        detect_left.ang_from_bot_rad = math.radians(angle_deg)
        detect_left.dis_from_bot_in = dis_in


        return detect_left
    else:
        # otherwise just return one of them (left cause I'm left handed)
        return detect_left


        

       

if __name__ == "__main__":
    main()