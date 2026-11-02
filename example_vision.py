from tam_frame import get_field_frame, load_image_as_frame, show_frame, load_video_as_list_of_frames
from tam_hsv import load_search_dict_from_csv
from tam_vision import example_vision_full_stack
import cv2



def vision_full_stack_one_frame():
    frame_camera = load_image_as_frame("training_data/red_ball_centerframe.png")
    frame_field = get_field_frame(USE_DRAWN_FIELD= False)

    search_dict = load_search_dict_from_csv()

    frame_full = example_vision_full_stack(frame_field= frame_field, frame_camera=frame_camera, search_dict= search_dict)

    show_frame(frame_full)


def vision_full_stack_video():
    frame_field = get_field_frame(USE_DRAWN_FIELD= False)
    search_dict = load_search_dict_from_csv()

    list_frames_camera = load_video_as_list_of_frames("training_data/red_ball_vid.h264")

    for frame_camera in list_frames_camera:
        frame_full = example_vision_full_stack(frame_field= frame_field.copy(), frame_camera=frame_camera, search_dict=search_dict)

        cv2.imshow("Vision Stack", frame_full)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break




# Example usage
if __name__ == "__main__":

    vision_full_stack_one_frame()

    vision_full_stack_video()