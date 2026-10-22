import cv2
import numpy as np
from classes import FieldState
from tam_library import check_button, load_video_as_list_of_frames
from constants import NEW_MATCH


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

    list_frames = load_video_as_list_of_frames(video_path)

    for frame in list_frames:
        frame : np.ndarray


    # get the past n field_states and determine average positions of objects

    # determine whether to move or shoot

    # if moving, determine the desired position on the field

    # generate a path from current position to desired position

    # determine commands to arduino to follow the path