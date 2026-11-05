import numpy as np
from picamera2 import Picamera2
from tam_constants import CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y, CAMERA_CAPTURE_FPS


picam_horizontal_fov_deg = 62.2

CAM_LEFT = "LEFT_CAM"
CAM_RIGHT = "RIGHT_CAM"

CAM_LEFT_ID = 0
CAM_RIGHT_ID = 1



'''Library file for all functions related to binocular (two eye) vision'''


def setup_left_right_cams() -> tuple[Picamera2, Picamera2]:
    '''get the picamera class instances'''
    # Configure both cameras.
    left_cam = Picamera2(CAM_LEFT_ID)
    right_cam = Picamera2(CAM_RIGHT_ID)

    config = {
        "main": {
            "size": (CAMERA_CAPTURE_X, CAMERA_CAPTURE_Y),
            "format": "RGB888",  # OpenCV expects BGR; convert below.
        },
        "controls": {"FrameRate": CAMERA_CAPTURE_FPS},
    }

    left_cam.configure(left_cam.create_video_configuration(**config))
    right_cam.configure(right_cam.create_video_configuration(**config))
    left_cam.start()
    right_cam.start()

    return left_cam, right_cam




def closeout_left_right_cams(left_cam : Picamera2, right_cam : Picamera2):
    left_cam.stop()
    right_cam.stop()




def get_left_right_frames(cam_left : Picamera2, cam_right : Picamera2) -> dict[str, np.ndarray]:
    '''from the instances, return a dict of CAM_LEFT : left frame and CAM_RIGHT : right frame'''

    frame_left = cam_left.capture_array()
    frame_right = cam_right.capture_array()


    return_dict = {
        CAM_LEFT : frame_left,
        CAM_RIGHT : frame_right
    }

    return return_dict



def get_angle_of_object_deg(object_center_x_px : int) -> float:
    '''return the angle in degrees measured +ccw from the 3oclock position,
    object_center_x_px is the value in pixels of the object center from the left (0) of the screen'''


    return 0