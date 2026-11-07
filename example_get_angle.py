import cv2
from tam_frame import concat_frames, show_frame, resize_frame

def main():

    
    left_cam_vid = "training_data/1280_720_RIGHT_2026_11_5_13_28.mp4"
    right_cam_vid = "training_data/1280_720_LEFT_2026_11_5_13_28.mp4"

    capture_left = cv2.VideoCapture(left_cam_vid)
    capture_right = cv2.VideoCapture(right_cam_vid)

    # target time from the video
    target_seconds = 30 
    target_msec = target_seconds * 1000  

    # Set the video position to the desired millisecond
    capture_left.set(cv2.CAP_PROP_POS_MSEC, target_msec)
    capture_right.set(cv2.CAP_PROP_POS_MSEC, target_msec)
    success, frame_left = capture_left.read()
    success, frame_right = capture_right.read()


    frame = concat_frames(frame_left, frame_right, "DOWN")

    frame = resize_frame(frame, 0.6)

    show_frame(frame)

    capture_left.release()
    capture_right.release()
    pass



if __name__ == "__main__":
    main()