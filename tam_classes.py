from dataclasses import dataclass, field
from tam_constants import *
from tam_colors import RED, GREEN, FUCHSIA
import math


color_dict = {
    BALL_RED : RED,
    HAT_BLUE : BLUE,
    HAT_FUCHSIA : FUCHSIA,
    HAT_GREEN : GREEN,
    HAT_YELLOW : YELLOW
}


@dataclass
class Point:
    x: float = 0
    y: float = 0

    def __str__(self) -> str:
        return f"({round(self.x)},{round(self.y)})"

@dataclass
class Line:
    pt1 : Point = field(default_factory=lambda: Point(0, 0))
    pt2 : Point = field(default_factory=lambda: Point(0, 0))



def get_point_int_tuple(point: Point) -> tuple[int, int]:
    return (int(point.x), int(point.y))





@dataclass
class Rectangle:
    width: int = 0
    height: int = 0
    top_left: Point = field(default_factory=lambda: Point(0, 0))
    # center: Point = Point(top_left.x + width / 2, top_left.y + height / 2)



@dataclass
class Detection:
    name: str = "NO_NAME"
    in_frame: bool = False
    camera_pos_px : Point = field(default_factory=lambda: Point(0, 0))
    width_px : int = 0
    area_px : int = 0




@dataclass
class Settings:
    '''wrapper for the settings that affect how our match is run and drawn'''

    our_team_is_orange : bool = False
    left_is_green : bool = False
    right_is_purple : bool = False

    draw_arrow_to_ball: bool = True
    draw_our_bot : bool = True
    draw_ball : bool = True





def get_settings(our_team_is_orange: bool) -> Settings:
    # if our team is orange:
    # left is green and right is purple

    # if our team is yellow
    # left is purple and right is green

    set = Settings()

    if our_team_is_orange:
        set.our_team_is_orange = True
        set.left_is_green = True
        set.right_is_purple = True
    else:
        set.our_team_is_orange = False
        set.left_is_green = False
        set.right_is_purple = False

    return set

 




@dataclass
class CameraState:
    '''a class containing all the information pulled from the camera. EVERYTHING in pixels'''

    camera_x = CAMERA_CAPTURE_X #1280
    camera_y = CAMERA_CAPTURE_Y #720
    camera_fov_deg = 62.2

    is_left_camera : bool = True

    # define what was in frame
    ball_in_frame : bool = False
    tbot_in_frame : bool = False    

    gp_green_up_in_frame : bool = False    # up
    gp_green_dw_in_frame : bool = False    # down

    gp_purpl_up_in_frame : bool = False
    gp_purpl_dw_in_frame : bool = False

    our_goal_in_frame : bool = False
    their_goal_in_frame : bool = False

    # position of objects in the frame
    ball_pos_px : Point = field(default_factory=lambda: Point(0, 0))
    tbot_pos_px : Point = field(default_factory=lambda: Point(0, 0))

    gp_green_up_pos_px : Point = field(default_factory=lambda: Point(0, 0))
    gp_green_dw_pos_px : Point = field(default_factory=lambda: Point(0, 0))

    gp_purpl_up_pos_px : Point = field(default_factory=lambda: Point(0, 0))
    gp_purpl_dw_pos_px : Point = field(default_factory=lambda: Point(0, 0))

    # percieved width of objects in the frame (used for single cam distance detection)
    ball_width_px : float = 0
    tbot_width_px : float = 0
    gp_purpl_up_width_px : float = 0
    gp_purpl_dw_width_px : float = 0
    gp_green_up_width_px : float = 0
    gp_green_dw_width_px : float = 0


@dataclass
class DualCameraState:
    '''both camerastates packaged together'''

    left : CameraState = field(default_factory=lambda: CameraState())
    right : CameraState = field(default_factory=lambda: CameraState())




@dataclass
class FieldState:
    '''a class to contain all the information needed to draw the current state of the field. 
    EVERYTHING in inches or radians with respect to the field. Radians measured +ccw from field east '''

    timestep: float = 0

    # defining our bot
    our_bot_pos_in: Point = field(default_factory=lambda: Point(0, 0))
    our_bot_bearing_rad: float = BEARING_NORTH

    # defining their bot
    their_bot_pos_in: Point = field(default_factory=lambda: Point(0, 0))
    their_bot_bearing_rad: float = BEARING_SOUTH

    # defining the ball
    ball_pos_in: Point = field(default_factory=lambda: Point(0, 0))
    ball_vel_x_in_per_s : float = 0
    ball_vel_y_in_per_s : float = 0
    ball_is_ours : bool = False
    ball_is_theirs : bool = False




