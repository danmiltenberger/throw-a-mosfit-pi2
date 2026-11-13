import RPi.GPIO as GPIO  # type: ignore
from tam_pins import END_GAME_PIN, START_KICK_PIN, START_MATCH_PIN, CHANGE_GOAL_PIN, CHANGE_TEAM_PIN
from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_classes import Settings
from tam_switches import get_switches_status_dict, setup_switches
from tam_vision import get_list_detections, get_hsv_frame
from tam_hsv import load_search_dict_from_csv
from tam_decide import merge_list_detections, convert_detect_dict_to_fieldstate, get_init_fieldstate, get_bot_command
from tam_arduino import send_command_to_arduino
from tam_lcd import write_lcd_lines
from tam_draw import get_lcd_lines

def main():

    # setup switches
    setup_switches()

    # setup cameras
    camL, camR = setup_left_right_cams()

    # setup lcd

    # load the search dict
    search_dict = load_search_dict_from_csv()

    # load the initial fieldstate
    prev_fieldstate = get_init_fieldstate(is_penalty_kick=True)

    while True:

        # Guiding question - what is the simplest way to do this?
        # constantly send commands to arduino -> motor power controls if we go or not
        # look for BOTH yellow and blue hats and try to avoid both instead of fancy toggle searching
        # face forward as much as possible and assume the goal we see is the goal we should kick to

        switches_status = get_switches_status_dict()

        frameL, frameR = get_left_right_frames(cam_left=camL, cam_right= camR)

        # search the camera's for detections
        frame_cam_left_hsv = get_hsv_frame(frameL.copy())
        frame_cam_right_hsv = get_hsv_frame(frameR.copy())

        list_detections_left = get_list_detections(frame_cam_left_hsv, search_dict)
        list_detections_right = get_list_detections(frame_cam_right_hsv, search_dict)

        dict_detection_merged = merge_list_detections(list_detections_left, list_detections_right)
        fieldstate = convert_detect_dict_to_fieldstate(dict_detection_merged, prev_fieldstate=prev_fieldstate)

        bot_command, status_str = get_bot_command(fieldstate)

        # send the command
        send_command_to_arduino(bot_command)

        # write useful information to the LCD
        lcd_lines = get_lcd_lines(fieldstate)
        write_lcd_lines(lcd_lines)



        




if __name__ == "__main__":
    main()