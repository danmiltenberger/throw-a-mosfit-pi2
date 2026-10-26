from dataclasses import dataclass, field
from constants import *
from constants_rads import *
import math


@dataclass
class Point:
    x: float = 0
    y: float = 0

    def __str__(self) -> str:
        return f"({round(self.x)}, {round(self.y)})"

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
class DetectedObject:
    width_px: int = 0
    area_px: int = 0
    center_pos_on_screen_px: Point = field(default_factory=lambda: Point(0, 0))

    distance_from_bot: float = 0
    bearing_rad: float = 0

    pos_wrt_bot: Point = field(default_factory=lambda: Point(0, 0))

    def get_pos_wrt_bot(self):
        self.pos_wrt_bot.x = self.distance_from_bot * math.cos(self.bearing_rad)
        self.pos_wrt_bot.y = self.distance_from_bot * math.sin(self.bearing_rad)
        return

    def __str__(self) -> str:
        return f"obj(width_px: {self.width_px}, area_px: {self.area_px}, screen_center_px: {self.center_pos_on_screen_px})"
        pass


@dataclass
class FieldState:

    found_dict = {}

    timestep: float = 0

    our_bot_pos_in: Point = field(default_factory=lambda: Point(0, 0))
    our_bot_bearing_rad: float = BEARING_NORTH

    their_bot_pos_in: Point = field(default_factory=lambda: Point(0, 0))
    their_bot_bearing_rad: float = BEARING_SOUTH

    ball_pos_in: Point = field(default_factory=lambda: Point(0, 0))
    ball_vel_x_in_per_s : float = 0
    ball_vel_y_in_per_s : float = 0

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

        return f"State(our_bot_pos: {self.our_bot_pos_in}, their_bot_pos: {self.their_bot_pos_in}, ball_pos: {self.ball_pos_in})"
        pass


