import cv2
from picamera2 import Picamera2 #type: ignore
from tam_binocular import get_left_right_frames, setup_left_right_cams, CAM_LEFT, CAM_RIGHT, closeout_left_right_cams
from tam_frame import show_frame, concat_frames, get_field_frame, show_frame_in_loop
from run_match_from_video import match_two_cam_frame
from tam_hsv import load_search_dict_from_csv
from tam_decide import get_init_fieldstate
from tam_draw import get_lcd_frame_fieldstate
from tam_switches import setup_switches


def run_2cam():

    print("setting up cameras")
    cam_left, cam_right = setup_left_right_cams()

    print("setting up switches")
    setup_switches()

    print("loading search dict")
    search_dict = load_search_dict_from_csv()

    print("loading field frame")
    frame_field = get_field_frame()

    print("loading init fieldstate")
    prev_fieldstate = get_init_fieldstate()


    while True:
        frame_left, frame_right = get_left_right_frames(cam_left,cam_right)

        frame_cam, frame_field, fieldstate = match_two_cam_frame(
            frame_cam_left=frame_left, 
            frame_cam_right=frame_right, 
            frame_field=frame_field.copy(),
            prev_fieldstate=prev_fieldstate,
            search_dict=search_dict)


        prev_fieldstate = fieldstate

        frame_lcd = get_lcd_frame_fieldstate(fieldstate)

        # combine so top left is camera, bottom left is lcd, right is field
        frame = concat_frames(frame_cam, frame_lcd, "DOWN")
        frame = concat_frames(frame, frame_field)

        if show_frame_in_loop(frame) == False:
            break




if __name__ == "__main__":
    run_2cam()
