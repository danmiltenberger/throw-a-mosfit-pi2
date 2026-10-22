from dataclasses import dataclass
import numpy as np

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


folder_list = [TRAINING_DATA, FIELD_STATES]

# Color Constants
YELLOW_TEAM = "YELLOW"
BLUE_TEAM = "BLUE"
FUCHSIA_SIDE = "FUCHSIA"
GREEN_SIDE = "GREEN"


# visualization
PIXELS_PER_INCH : int = 5

@dataclass 
# default match settings
class MatchSettings:

    # Game states
    WAITING_FOR_START: bool = True

    # Game vars
    OUR_TEAM_COLOR: str = YELLOW_TEAM
    THEIR_TEAM_COLOR: str = BLUE_TEAM
    GOAL_EAST_COLOR: str = FUCHSIA_SIDE
    GOAL_WEST_COLOR: str = GREEN_SIDE





### colors
# OpenCV colors: (Blue, Green, Red)


# Black, white, and grays
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
GRAY        = (128, 128, 128)
LIGHT_GRAY  = (192, 192, 192)
DARK_GRAY   = (64, 64, 64)


# Goalpost specific colors
FUCHSIA = (255, 0, 255)  # OpenCV BGR: blue, green, red

# Primary and secondary colors
RED         = (0, 0, 255)
GREEN       = (0, 255, 0)
BLUE        = (255, 0, 0)
YELLOW      = (0, 255, 255)
CYAN        = (255, 255, 0)
MAGENTA     = (255, 0, 255)

# Additional colors
ORANGE      = (0, 165, 255)
PURPLE      = (128, 0, 128)
PINK        = (203, 192, 255)
BROWN       = (42, 42, 165)
GOLD        = (0, 215, 255)
NAVY        = (128, 0, 0)
TEAL        = (128, 128, 0)
OLIVE       = (0, 128, 128)
MAROON      = (0, 0, 128)

# Light colors
LIGHT_BLUE  = (230, 216, 173)
LIGHT_GREEN = (144, 238, 144)
LIGHT_PINK  = (193, 182, 255)

# Dark colors
DARK_RED    = (0, 0, 139)
DARK_GREEN  = (0, 100, 0)
DARK_BLUE   = (139, 0, 0)



#### quick look up

search_dict = {
    BALL_RED: {
        DRAW_COLOR: RED,
        HSV_HI: np.array([0, 200, 0], dtype=np.uint8),
        HSV_LO: np.array([10, 255, 157], dtype=np.uint8),
        KNOWN_WIDTH: BALL_RED_DIAM_IN,
        ANALYSIS_SHAPE : CIRC,
    },
    BALL_YELLOW: {
        DRAW_COLOR: YELLOW,
        HSV_LO: np.array([21, 103, 170], dtype=np.uint8),
        HSV_HI: np.array([35, 201, 250], dtype=np.uint8),
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