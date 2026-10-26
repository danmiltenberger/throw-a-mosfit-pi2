import cv2
import numpy as np
from classes import FieldState
from tam_library import check_button, load_video_as_list_of_frames
from search_frame import get_fieldstate_from_frame
from tam_library_draw_field import draw_field_from_field_state, get_field_frame
from constants import NEW_MATCH
from constants_points import *
from constants_rads import *
import random
import math


def play_match():
    """play the match!"""

    while True:

        # check if match is over
        if check_button(NEW_MATCH):
            break   # go back to main loop and wait for next button

        # get the current frame

        # get the past n field_states and determine average positions of objects

        # determine whether to move or shoot

        # if moving, determine the desired position on the field

        # generate a path from current position to desired position

        # determine commands to arduino to follow the path



    # TODO
    pass


def play_virtual_match(video_path: str):
    '''
    'play' the match with each frame from a given video. 
    NO realtime sensor correction
    '''

    #### One time setup

    list_frames = load_video_as_list_of_frames(video_path)

    # set the initial position with some randomness involved
    random_x_offset = random.randint(a=-5, b=5)
    random_y_offset = random.randint(a=-5, b=5)
    ten_degrees_as_rad = round(math.radians(10))
    random_bearing_offset = random.randint(-ten_degrees_as_rad, ten_degrees_as_rad)

    start_position = Point(
        x= FIELD_GOALBOX_CENTER_BOTTOM.x + random_x_offset,
        y= FIELD_GOALBOX_CENTER_BOTTOM.y + random_y_offset
    )

    initial_state = FieldState(
        ball_is_ours= False,
        ball_is_theirs=False,
        ball_pos_in= FIELD_CENTER,
        our_bot_pos_in= start_position,
        our_bot_bearing_rad= BEARING_NORTH + random_bearing_offset,
    )

    field_frame = get_field_frame()

    #### Loop through the frames
    for frame in list_frames:
        frame : np.ndarray

        field_state = get_fieldstate_from_frame(frame)

        field_frame = draw_field_from_field_state(field_frame= field_frame, state= field_state)


    # get the past n field_states and determine average positions of objects

    # determine whether to move or shoot

    # if moving, determine the desired position on the field

    # generate a path from current position to desired position

    # determine commands to arduino to follow the path