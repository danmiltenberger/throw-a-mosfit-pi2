import cv2
from picamera2 import Picamera2
from tam_binocular import get_left_right_frames, setup_left_right_cams, CAM_LEFT, CAM_RIGHT
from tam_frame import show_frame, concat_frames


def run_2cam():
    cam_left, cam_right = setup_left_right_cams()

    show_two_cam(cam_left, cam_right)




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
