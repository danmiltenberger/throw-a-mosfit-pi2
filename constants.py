from dataclasses import dataclass
from classes import Point, Line
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


### Defining the field, everything in inches
FIELD_CENTER = Point(48,72)

GOALPOST_SOUTHWEST = Point(24,0)
GOALPOST_SOUTHEAST = Point(72,0)
GOALPOST_NORTHWEST = Point(24,144)
GOALPOST_NORTHEAST = Point(72,144)

FIELD_SOUTHWEST_CORNER = Point(0,0)
FIELD_SOUTHEAST_CORNER = Point(96,0)
FIELD_NORTHWEST_CORNER = Point(0,144)
FIELD_NORTHEAST_CORNER = Point(96,144)

# octogon points
# top
OCTOGON_1 = Point(12,144)
OCTOGON_2 = Point(84, 144)

# right
OCTOGON_3 = Point(96, 132)
OCTOGON_4 = Point(96, 12)

# bottom
OCTOGON_5 = Point(84, 0)
OCTOGON_6 = Point(12,0)

# left
OCTOGON_7 = Point(0,12)
OCTOGON_8 = Point(0, 132)

# define the lines that make up the octagon
line_goal_top = Line(
    pt1= GOALPOST_NORTHWEST,
    pt2= GOALPOST_NORTHEAST
)

line_topright_horizontal = Line(
    pt1= GOALPOST_NORTHEAST,
    pt2= OCTOGON_2,
)

line_topright_diag = Line(
    pt1= OCTOGON_2,
    pt2= OCTOGON_3
)

line_right_vert = Line(
    pt1= OCTOGON_3,
    pt2= OCTOGON_4
)

line_botright_diag = Line(
    pt1= OCTOGON_4,
    pt2= OCTOGON_5
)

line_botright_horiontal = Line(
    pt1= OCTOGON_5,
    pt2= GOALPOST_SOUTHEAST
)

line_goal_bot = Line(
    pt1= GOALPOST_SOUTHEAST,
    pt2= GOALPOST_SOUTHWEST,
)

line_botleft_horizontal = Line(
    pt1= GOALPOST_SOUTHWEST,
    pt2= OCTOGON_6
)

line_botleft_diag = Line(
    pt1= OCTOGON_6,
    pt2= OCTOGON_7
)

line_left_vert = Line(
    pt1= OCTOGON_7,
    pt2= OCTOGON_8
)

line_topleft_horizontal = Line(
    pt1= OCTOGON_8,
    pt2= GOALPOST_NORTHWEST
)


perim_octogon : list = [
    OCTOGON_1, OCTOGON_2, OCTOGON_3, OCTOGON_4, OCTOGON_5, OCTOGON_6, OCTOGON_7, OCTOGON_8
]