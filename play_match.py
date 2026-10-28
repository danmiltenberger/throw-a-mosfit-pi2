import cv2
import numpy as np
from classes import FieldState, BotCommand
from tam_library import check_button, load_video_as_list_of_frames
from search_frame import get_fieldstate_from_frame
from tam_library_draw_field import draw_field_from_field_state, get_field_frame
from constants import NEW_MATCH
from constants_points import *
from constants_rads import *
import random
import math
from bot_decisions import get_bot_command


def play_match(vid_path: str = ""):
    """play the match either from a live feed or from a pre-recorded video"""

    list_fieldstates = []


    frame_index : int = 0
    if vid_path != "":
        list_frames = load_video_as_list_of_frames(vid_path)
        is_load_frame = True
    else:
        list_frames = []

    while True:

        # check if match is over
        if check_button(NEW_MATCH):
            break   # go back to main loop and wait for next button

        # get the current camera
        frame = list_frames[frame_index]

        # get the fieldstate from the frame
        this_fieldstate = get_fieldstate_from_frame(frame)

        # get the past n field_states and determine average positions of objects
        avg_fieldstate = get_average_fieldstate(this_fieldstate, list_fieldstates)

        bot_command, status = get_bot_command(avg_fieldstate)
        send_to_arduino(bot_command)
        

    pass



def get_average_fieldstate(this_fieldstate: FieldState, list_prev : list[FieldState]) -> FieldState:


    # with the new fieldstate, consider if individual pieces of data are worth keeping


    # blend to get an average position for different objects

    return this_fieldstate


def get_frame_from_pi():

    # FIX THIS
    # TODO
    return


def send_to_arduino(bot_command: BotCommand):
    pass