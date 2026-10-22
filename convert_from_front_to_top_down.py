from classes import Point
from constants import SCREEN_CENTER_X
import math


FOCAL_LENGTH = 1253.333     # recalc this when able


def calc_distance_from_bot(known_width_in: float, percieved_width_px) -> float:

    Z = (known_width_in * FOCAL_LENGTH) / percieved_width_px
    return Z



def calc_angle_from_screen_center(point: Point) -> float:

    pixel_x = point.x
    delta_x = pixel_x - SCREEN_CENTER_X

    return -math.atan2(delta_x, FOCAL_LENGTH)