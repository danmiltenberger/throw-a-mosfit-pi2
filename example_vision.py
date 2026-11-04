
import cv2
from time import sleep
from tam_classes import FieldState, Detection
from tam_frame import get_field_frame, load_image_as_frame, show_frame, load_video_as_list_of_frames, concat_frames
from tam_hsv import load_search_dict_from_csv
from tam_vision import example_vision_full_stack, get_fieldstate_from_frame, get_annotated_frame, get_hsv_frame, get_list_detections
from tam_draw import draw_fieldstate, draw_detection_list_to_camera_frame
from tam_decide import convert_detect_list_to_fieldstate, get_init_fieldstate
from tam_constants import BALL_RED, MIN_AREA_PX
from tam_points import FIELD_CENTER
from tam_colors import BLUE, YELLOW

def main():
    vid_path = "training_data/2026_11_02_T_15_35_52.mp4"
    vision_and_decision_from_vid(vid_path)




def vision_and_decision_from_photo(photo_path: str):
    photo_path = "hsv_photos/goalposts_and_ball.png"
    photo_path = "hsv_photos/hat_blue.png"
    photo_path = "hsv_photos/hat_yellow.png"

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