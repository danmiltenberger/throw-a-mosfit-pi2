import cv2
from picamera2 import Picamera2 #type: ignore
from tam_binocular import get_left_right_frames, setup_left_right_cams, CAM_LEFT, CAM_RIGHT, closeout_left_right_cams
from tam_frame import show_frame, concat_frames, get_field_frame, show_frame_in_loop
from run_match_from_video import match_two_cam_frame
from tam_hsv import load_search_dict_from_csv
from tam_decide import get_init_fieldstate


def run_2cam():
    print(f"running file {__name__}")
    cam_left, cam_right = setup_left_right_cams()

    search_dict = load_search_dict_from_csv()
    frame_field = get_field_frame()
    prev_fieldstate = get_init_fieldstate()


    while True:
        frame_dict = get_left_right_frames(cam_left,cam_right)
        frame_left = frame_dict[CAM_LEFT]
        frame_right = frame_dict[CAM_RIGHT]

        frame, fieldstate = match_two_cam_frame(
            frame_cam_left=frame_left, 
            frame_cam_right=frame_right, 
            frame_field=frame_field.copy(),
            prev_fieldstate=prev_fieldstate,
            search_dict=search_dict)


        prev_fieldstate = fieldstate

        if show_frame_in_loop(frame) == False:
            break





def show_two_cam(left_cam: Picamera2, right_cam: Picamera2):

    while True:
        frames_dict =  get_left_right_frames(cam_left= left_cam, cam_right=right_cam)

        frame_left = frames_dict[CAM_LEFT]
        frame_right = frames_dict[CAM_RIGHT]

        left_right = concat_frames(frame_left, frame_right)

        cv2.imshow("left_right", left_right)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


    pass


if __name__ == "__main__":
    run_2cam()
