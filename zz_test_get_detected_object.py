from tam_library_analyze_camera import get_detected_object
from classes import DetectedObject
from tam_library import load_image_as_frame


def test_get_detected_object():
    file_name = "red_ball_centerframe"
    file_path = "training_data/" + file_name + ".png"

    camera_frame = load_image_as_frame(file_path)

    