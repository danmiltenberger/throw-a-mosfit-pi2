import numpy as np
from tam_colors import *

# Camera Constants
CAMERA_CAPTURE_X = 640
CAMERA_CAPTURE_Y = 480
CAMERA_CAPTURE_FPS = 30
SCREEN_CENTER_X = int(CAMERA_CAPTURE_X /2)
SCREEN_CENTER_Y = int(CAMERA_CAPTURE_Y /2)

# Button Constants
CHANGE_TEAM = "CHANGE_TEAM"
NEW_MATCH = "NEW_MATCH"
PENALTY_KICK = "PENALTY_KICK"
START_GAME = "START_GAME"

### button pins
START_MATCH_PIN = 26
START_KICK_PIN = 19
CHANGE_TEAM_PIN = 13
CHANGE_GOAL_PIN = 6
END_GAME_PIN = 5


# dictionary keys
OUR_TEAM_COLOR = "OUR_TEAM_COLOR"
OUR_LEFT_GOAL = "OUR_LEFT_GOAL"
HEADER_ROW = "HEADER_ROW"
BUTTON_STATUS = "BUTTON_STATUS"

# dict vals
GOAL_GREEN = "GRE"
GOAL_PURPLE = "PUR"
TEAM_YELLOW = "YEL"
TEAM_BLUE = "BLU"

HEADER_WAITING = "Change settings or start"

status_str = "not read"

match_settings = {
    OUR_LEFT_GOAL : GOAL_GREEN,
    OUR_TEAM_COLOR : TEAM_YELLOW,
    HEADER_ROW : HEADER_WAITING,
    BUTTON_STATUS : status_str,
}

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

# dictionary keys keys
KNOWN_WIDTH = "KNOWN_WIDTH"
MIN_AREA_PX = "MIN_AREA_PX"
DRAW_COLOR = "DRAW_COLOR"
HSV_LO = "HSV_LO"
HSV_HI = "HSV_HI"
ANALYSIS_SHAPE = "ANALYSIS_SHAPE"
RADIUS_IN = "RADIUS_IN"
WIDTH_PX = "WIDTH_PX"
AREA_PX = "AREA_PX"
SHAPE = "SHAPE"
CENTER_X_PX = "CENTER_X_PX"
CENTER_Y_PX = "CENTER_Y_PX"
OBJECT_NAME = "OBJECT_NAME"

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

# path to hsv csv to be used
HSV_CSV_PATH = "hsv_bounds/classroom.csv"



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


