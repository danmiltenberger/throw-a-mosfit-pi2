from tam_frame import show_frame
import cv2
import numpy as np

def main():

    left_cam_vid = "training_data/1280_720_RIGHT_2026_11_5_13_28.mp4"
    right_cam_vid = "training_data/1280_720_LEFT_2026_11_5_13_28.mp4"

    cap = cv2.VideoCapture(left_cam_vid)

    # Define your target timestep in seconds
    target_seconds = 12.5  
    # Convert to milliseconds
    target_msec = target_seconds * 1000  

    # Set the video position to the desired millisecond
    cap.set(cv2.CAP_PROP_POS_MSEC, target_msec)
    success, frame = cap.read()
    show_frame(frame)


    cap.release()

    


if __name__ == "__main__":
    main()