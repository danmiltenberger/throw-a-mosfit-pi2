from field_state_save_and_load import load_fieldstates_from_csv
from tam_library_draw_field import get_field_frame, draw_field_from_field_state
from tam_library import show_frame
import cv2


def main():
    file_name = "bot_on_field"
    fieldstate_csvpath = f"field_states/{file_name}.csv"
    play_field_frame_csv(fieldstate_csvpath, file_name)


def play_field_frame_csv(fieldstate_csv_path, window_name: str = "Frame"):

    list_of_states = load_fieldstates_from_csv(fieldstate_csv_path)

    original_field_frame = get_field_frame()

    for state in list_of_states:
        copy_field = original_field_frame.copy()
        copy_field = draw_field_from_field_state(field_frame=copy_field, state=state)

        cv2.imshow(mat=copy_field, winname=window_name)

        key = cv2.waitKey(10) & 0xFF

        if key in (27, ord("q")):
            break

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break


if __name__ == "__main__":
    main()
