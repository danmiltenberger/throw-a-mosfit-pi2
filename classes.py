from dataclasses import dataclass, field
from constants import *
import math


@dataclass
class Point:
    x: float = 0
    y: float = 0

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"



def get_point_int_tuple(point: Point) -> tuple[int,int]:
    return (int(point.x), int(point.y))

@dataclass
class Rectangle:
    width: int = 0
    height: int = 0
    top_left: Point = field(default_factory=lambda: Point(0, 0))
    #center: Point = Point(top_left.x + width / 2, top_left.y + height / 2)


@dataclass
class DetectedObject:
    width_px : int = 0
    area_px : int = 0
    center_pos_on_screen_px: Point = field(default_factory=lambda: Point(0, 0))

    distance_from_bot : float = 0
    bearing_rad : float = 0

    pos_wrt_bot : Point = field(default_factory=lambda: Point(0, 0))

    def get_pos_wrt_bot(self):
        self.pos_wrt_bot.x = self.distance_from_bot * math.cos(self.bearing_rad)
        self.pos_wrt_bot.y = self.distance_from_bot * math.sin(self.bearing_rad)
        return




@dataclass
class FieldState:

    found_dict  = {
        BALL_RED : False,
        BALL_YELLOW : False,
        HAT_BLUE : False,
        HAT_YELLOW : False,
        HAT_FUCHSIA : False,
        HAT_GREEN : False,
    }


    timestep: float = 0

    our_bot_pos_in: Point = field(default_factory=lambda: Point(0, 0))
    our_bot_bearing_rad: float = 0

    their_bot_pos_in: Point = field(default_factory=lambda: Point(0, 0))
    their_bot_bearing_rad: float = 0

    ball_pos_in: Point = field(default_factory=lambda: Point(0, 0))

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
