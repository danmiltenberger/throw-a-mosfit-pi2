
import cv2
from tam_classes import FieldState
from tam_frame import get_field_frame, load_image_as_frame, show_frame, load_video_as_list_of_frames, concat_frames
from tam_hsv import load_search_dict_from_csv
from tam_vision import example_vision_full_stack, get_fieldstate_from_frame, get_annotated_frame
from tam_draw import draw_fieldstate


def main():
    # vid_path = "training_data/2026_11_02_T_15_35_52.mp4"
    # vision_and_decision_from_vid(vid_path)

    photo_path = "hsv_photos/goalposts_and_ball.png"

    vision_and_decision_from_photo(photo_path)



def vision_and_decision_from_photo(photo_path: str):
    frame_field = get_field_frame()
    search_dict = load_search_dict_from_csv()

    frame_camera = load_image_as_frame(photo_path)

    frame_annotated = get_annotated_frame(frame_camera, search_dict= search_dict)

    prev_fieldstate = FieldState()

    this_fieldstate = get_fieldstate_from_frame(frame= frame_camera, prev_fieldstate=prev_fieldstate, search_dict= search_dict)

    frame_field = draw_fieldstate(field_frame=frame_field.copy(), fieldstate=this_fieldstate)


    side_by_side = concat_frames(frame_annotated, frame_field, "RIGHT")

    show_frame(side_by_side)


    


def vision_and_decision_from_vid(vid_path: str):
    frame_field = get_field_frame(USE_DRAWN_FIELD= False)
    search_dict = load_search_dict_from_csv()

    list_frames_camera = load_video_as_list_of_frames(vid_path)

    prev_fieldstate = FieldState()

    for frame_camera in list_frames_camera:

        this_fieldstate = get_fieldstate_from_frame(frame= frame_camera, prev_fieldstate=prev_fieldstate, search_dict= search_dict)

        frame_field = draw_fieldstate(field_frame=frame_field.copy(), fieldstate=this_fieldstate)


        side_by_side = concat_frames(frame_camera.copy(), frame_field, "RIGHT")

        cv2.imshow("Side by side", side_by_side)


        prev_fieldstate = this_fieldstate
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break








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

    main()