import numpy as np
import cv2
from tam_frame import load_video_as_list_of_frames, get_field_frame, concat_frames, resize_frame, show_frame_in_loop, show_frame, load_image_as_frame
from tam_hsv import load_search_dict_from_csv
from tam_vision import get_list_detections, get_hsv_frame
from tam_draw import draw_detection_list_to_camera_frame, add_text_top, draw_two_cams_to_one, draw_fieldstate
from tam_decide import merge_list_detections, convert_detect_dict_to_fieldstate, get_init_fieldstate
from tam_classes import FieldState
from tam_colors import BLUE



# all of the functionality of run_match, but instead of getting the frame live, feed it a frame from video file(s)





def main():
    # yea I know these are mislabeled, but I think they were just saved the wrong way  
    # right_cam_vid = "training_data/1280_720_RIGHT_2026_11_5_13_28.mp4"
    # left_cam_vid = "training_data/1280_720_LEFT_2026_11_5_13_28.mp4"

    # match_two_cam(left_cam_vid_path= left_cam_vid, right_cam_vid_path= right_cam_vid)

    frame_left = load_image_as_frame("hsv_photos/all_in_one_left.png")
    frame_right = load_image_as_frame("hsv_photos/all_in_one_right.png")

    search_dict = load_search_dict_from_csv()
    frame_field_original = get_field_frame(left_is_green= True)
    prev_fieldstate = get_init_fieldstate()


    frame, fieldstate = match_two_cam_frame(
        prev_fieldstate= prev_fieldstate,
        search_dict= search_dict,
        frame_field= frame_field_original,
        frame_cam_right= frame_right,
        frame_cam_left= frame_left,
    )

    show_frame(frame)




def match_two_cam(left_cam_vid_path: str, right_cam_vid_path: str, window_resize_mult : float = 0.6, fps: int = 30):

    # load the top down view and search dict
    search_dict = load_search_dict_from_csv()
    frame_field_original = get_field_frame(left_is_green= True)

    prev_fieldstate = get_init_fieldstate()

    # load the videos
    frame_list_left = load_video_as_list_of_frames(left_cam_vid_path)
    frame_list_right = load_video_as_list_of_frames(right_cam_vid_path)
    min_list_frames = min(len(frame_list_left), len(frame_list_right))

    frame_to_show_at_end = frame_field_original

    # iterate through the videos
    for i in range(min_list_frames):

        # get this iteration's left, right, and field frame
        frame_field = frame_field_original.copy()
        frame_cam_left = frame_list_left[i]
        frame_cam_right = frame_list_right[i]


        frame, fieldstate = match_two_cam_frame(frame_cam_left, frame_cam_right, frame_field, search_dict, prev_fieldstate)
        prev_fieldstate = fieldstate

        # vid duration is frames / frames per sec
        duration_sec = i / fps
        frame_label = f"frame {i}/{min_list_frames} at {fps}fps sec:{round(duration_sec,1)} "
        frame = add_text_top(frame, frame_label)

        

        frame = resize_frame(frame, window_resize_mult)
        frame_to_show_at_end = frame

        if show_frame_in_loop(frame) == False:
            break

    show_frame(frame_to_show_at_end)


def match_two_cam_frame(
        frame_cam_left : np.ndarray, 
        frame_cam_right: np.ndarray, 
        frame_field: np.ndarray, 
        search_dict: dict, 
        prev_fieldstate: FieldState) -> tuple[np.ndarray, FieldState]:
    
    # search the camera's for detections
    frame_cam_left_hsv = get_hsv_frame(frame_cam_left.copy())
    frame_cam_right_hsv = get_hsv_frame(frame_cam_right.copy())

    list_detections_left = get_list_detections(frame_cam_left_hsv, search_dict)
    list_detections_right = get_list_detections(frame_cam_right_hsv, search_dict)

    # draw both lists to the left frame (for simplicity)
    frame_cam_left = draw_two_cams_to_one(frame_cam_left, list_detections_left, list_detections_right)

    # try to merge the detections into a fieldstate 
    dict_detection_merged = merge_list_detections(list_detections_left, list_detections_right)
    fieldstate = convert_detect_dict_to_fieldstate(dict_detection_merged, prev_fieldstate=prev_fieldstate)

    # draw the fieldstate to the field
    frame_field = draw_fieldstate(frame_field, fieldstate, draw_arrows=True)

    frame = concat_frames(frame_cam_left, frame_field)

    return frame, fieldstate




if __name__ == "__main__":
    main()