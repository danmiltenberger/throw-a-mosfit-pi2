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
    '''wrapper for the settings that affect how our match is run'''

    our_team_is_yellow : bool = True
    west_goalpost_is_green : bool = True

    search_list = [
        BALL_RED,
        HAT_BLUE,
        HAT_YELLOW,
        HAT_FUCHSIA,
        HAT_GREEN
    ]




@dataclass
class CameraState:
    '''a class containing all the information pulled from the camera. EVERYTHING in pixels'''

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
class GantryState:
    '''a class containing all the information pulled from both cameras both facing forward.
    EVERYTHING in inches and radians with respect to the center of the gantry'''

    camera_center_to_center_in : float = 5

    ball_dis_in : float = 500
    tbot_dis_in : float = 500
    gpgr_dis_in : float = 500
    gppr_dis_in : float = 500

    ball_rad : float = 0
    tbot_rad : float = 0
    gpgr_rad : float = 0
    gppr_rad : float = 0




@dataclass
class FieldState:
    '''a class to contain all the information needed to draw the current state of the field. 
    EVERYTHING in inches or radians with respect to the field '''

    timestep: float = 0


    # defining the match
    our_team_color : tuple[int,int,int] = YELLOW
    their_team_color : tuple[int,int,int] = BLUE
    our_west_goalpost : tuple[int,int,int] = PURPLE

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

    # defining what we saw from the frame
    ball_is_seen : bool = False
    their_bot_is_seen : bool = False
    goalpost_purple_is_seen : bool = False
    goalpost_green_is_seen : bool = False

    # defining the 'capture zone' where if the ball is within this zone it is considered captured
    our_bot_capture_zone_dis_ahead_in : float = 10
    our_bot_capture_zone_radius : float = 5
    capture_zone_center: Point = field(default_factory=lambda: Point(0, 0))

    # define what position and bearing the bot wants to achieve
    our_bot_target_pos : Point = field(default_factory=lambda: Point(0, 0))
    our_bot_target_rad : float = 0
    angle_to_target : float = 0

    # defining what goal the bot is trying to do, and the command sent to the arduino to do it
    status_str : str = "INITIAL"
    com_str : str ="_"
    com_dur_sec : float = 0

    def to_dict(self) -> dict:
        field_state_dict = {
            TIMESTEP: self.timestep,
            OUR_BOT_POS_IN_X: self.our_bot_pos_in.x,
            OUR_BOT_POS_IN_Y: self.our_bot_pos_in.y,
            OUR_BOT_BEARING: self.our_bot_bearing_rad,
            THEIR_BOT_POS_IN_X: self.their_bot_pos_in.x,
            THEIR_BOT_POS_IN_Y: self.their_bot_pos_in.y,
            THEIR_BOT_BEARING: self.their_bot_bearing_rad,
        }

        return field_state_dict

    def from_dict(self, new_dict: dict):
        self.timestep = new_dict[TIMESTEP]
        self.our_bot_pos_in.x = new_dict[OUR_BOT_POS_IN_X]
        self.our_bot_pos_in.y = new_dict[OUR_BOT_POS_IN_Y]
        self.our_bot_bearing_rad = new_dict[OUR_BOT_BEARING]
        self.their_bot_pos_in.x = new_dict[THEIR_BOT_POS_IN_X]
        self.their_bot_pos_in.y = new_dict[THEIR_BOT_POS_IN_Y]
        self.their_bot_bearing_rad = new_dict[THEIR_BOT_BEARING]

    def __str__(self) -> str:

        line1 = f"State {round(self.timestep,2)}sec ["
        line2 = f"Bot: {self.our_bot_pos_in}in, {round(math.degrees(self.our_bot_target_rad))}deg"
        line3 = f"Ball: {self.ball_pos_in}, Them: {self.their_bot_pos_in}]"

        return f"{line1}\n{line2}\n{line3}\n"

        #return f"State(our_bot_pos: {self.our_bot_pos_in}, their_bot_pos: {self.their_bot_pos_in}, ball_pos: {self.ball_pos_in})"
    

def get_capture_zone_point(state: FieldState) -> FieldState:

    capture_zone_center : Point = Point(
        x= state.our_bot_capture_zone_dis_ahead_in * math.cos(state.our_bot_bearing_rad) + state.our_bot_pos_in.x,
        y= state.our_bot_capture_zone_dis_ahead_in * math.sin(state.our_bot_bearing_rad) + state.our_bot_pos_in.y,
    )

    state.capture_zone_center = capture_zone_center
    return state




