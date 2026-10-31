import numpy as np
from tam_colors import *



# Camera Constants
CAMERA_CAPTURE_X = 640
CAMERA_CAPTURE_Y = 480
SCREEN_CENTER_X = int(CAMERA_CAPTURE_X /2)
SCREEN_CENTER_Y = int(CAMERA_CAPTURE_Y /2)

# Button Constants
CHANGE_TEAM = "CHANGE_TEAM"
NEW_MATCH = "NEW_MATCH"
PENALTY_KICK = "PENALTY_KICK"
START_GAME = "START_GAME"

# Folder Constants
TRAINING_DATA = "training_data"
FIELD_STATES = "field_states"
HSV_BOUNDS = "hsv_bounds"

# Field State Headers
TIMESTEP = "timestep"
OUR_BOT_POS_IN_X = "us_in_x"
OUR_BOT_POS_IN_Y = "us_in_x"
OUR_BOT_BEARING = "us_bearing_rad"
THEIR_BOT_POS_IN_X = "them_in_x"
THEIR_BOT_POS_IN_Y = "them_in_y"
THEIR_BOT_BEARING = "them_bearing_rad"

# Objects to search for constants
BALL_RED = "BALL_RED"
BALL_YELLOW = "BALL_YELLOW"
HAT_BLUE = "HAT_BLUE"
HAT_YELLOW = "HAT_YELLOW"
HAT_FUCHSIA = "HAT_FUCHSIA"
HAT_GREEN = "HAT_GREEN"

# known keys
KNOWN_WIDTH = "KNOWN_WIDTH"
MIN_AREA_PX = "MIN_AREA_PX"
DRAW_COLOR = "DRAW_COLOR"
HSV_LO = "HSV_LO"
HSV_HI = "HSV_HI"
ANALYSIS_SHAPE = "ANALYSIS_SHAPE"
RADIUS_IN = "RADIUS_IN"

# known widths
BALL_RED_DIAM_IN : float = 7
BALL_RED_RADIUS_IN : float = 7/2
BALL_YELLOW_DIAM_IN : float = 2.7
HAT_DIAM_IN : float = 8
GOALPOST_DIAM_IN : float = 8
GOALPOST_RADIUS_IN : int = int(GOALPOST_DIAM_IN/2)

BOT_DIAM_IN = 14
BOT_RADIUS_IN = 7

# ways to analyze
RECT = "RECT"
CIRC = "CIRC"


folder_list = [TRAINING_DATA, FIELD_STATES, HSV_BOUNDS]

# Color Constants
YELLOW_TEAM = "YELLOW"
BLUE_TEAM = "BLUE"
FUCHSIA_SIDE = "FUCHSIA"
GREEN_SIDE = "GREEN"


search_dict = {
    BALL_RED: {
        DRAW_COLOR: RED,
        HSV_LO: np.array([169, 213, 67], dtype=np.uint8),
        HSV_HI: np.array([179, 255, 147], dtype=np.uint8),
        KNOWN_WIDTH: BALL_RED_DIAM_IN,
        ANALYSIS_SHAPE : CIRC,
    },
    BALL_YELLOW: {
        DRAW_COLOR: YELLOW,
        HSV_HI: np.array([33, 207, 226]),
        HSV_LO: np.array([13, 127, 146]),
        KNOWN_WIDTH: BALL_YELLOW_DIAM_IN,
        ANALYSIS_SHAPE : CIRC,
    },
    HAT_BLUE: {
        DRAW_COLOR: BLUE,
        HSV_LO: np.array([90, 163, 125], dtype=np.uint8),
        HSV_HI: np.array([110, 255, 205], dtype=np.uint8),
        KNOWN_WIDTH: HAT_DIAM_IN,
        ANALYSIS_SHAPE : RECT,
    },
    HAT_YELLOW: {
        DRAW_COLOR: YELLOW,
        HSV_LO: np.array([22, 150, 174], dtype=np.uint8),
        HSV_HI: np.array([42, 210, 228], dtype=np.uint8),
        KNOWN_WIDTH: HAT_DIAM_IN,
        ANALYSIS_SHAPE : RECT,
    },
    HAT_FUCHSIA: {
        DRAW_COLOR: FUCHSIA,
        HSV_LO: "to_be_determined",
        HSV_HI: "to_be_determined",
        KNOWN_WIDTH: HAT_DIAM_IN,
        ANALYSIS_SHAPE : RECT,
    },
    HAT_GREEN: {
        DRAW_COLOR: GREEN,
        HSV_LO: "to_be_determined",
        HSV_HI: "to_be_determined",
        KNOWN_WIDTH: HAT_DIAM_IN,
        ANALYSIS_SHAPE : RECT,
    },
}


# direction constants
# measured ccw+ from 3oclock position
BEARING_EAST : float = 0
BEARING_NORTH : float = np.pi/2
BEARING_WEST : float = np.pi
BEARING_SOUTH : float = -np.pi/2

BEARING_NORTH_EAST : float = np.pi/4
BEARING_NORTH_WEST : float = np.pi/2 + np.pi /4
BEARING_SOUTH_EAST : float = - np.pi/4
BEARING_SOUTH_WEST : float = -np.pi/2 - np.pi/4 


