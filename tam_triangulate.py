import numpy as np
import math
from tam_classes import Point
from tam_topdown import calc_angle_from_screen_center, convert_angle_from_screen_center_to_ccw_east
from dataclasses import field, dataclass


@dataclass
class Triangle:
    side_a : float = 0
    side_b : float = 0
    side_c : float = 0
    rad_alpha : float = 0
    rad_beta : float = 0
    rad_gamma : float = 0
    pointA : Point = field(default_factory=lambda: Point(0, 0))
    pointB : Point = field(default_factory=lambda: Point(0, 0))
    pointC : Point = field(default_factory=lambda: Point(0, 0))

@dataclass
class Bearing:
    '''distance from the bot camera center and radian from +ccw bot east'''
    dis_in : float = 0
    rad : float = 0


def triangulate_object_wrt_bot(pos_px_left : Point, pos_px_right : Point) -> Point:
    '''return the x and y position of an object with respect to the bot'''

    # distance between cameras
    side_c = 5
    half_side_c = side_c /2
    
    rad_alpha = np.pi/2 - calc_angle_from_screen_center(pos_px_left)

    rad_beta  = np.pi/2 + calc_angle_from_screen_center(pos_px_right)

    # print("deg alpha", round(math.degrees(rad_alpha),1))
    # print("deg beta", round(math.degrees(rad_beta),1))


    rad_gamma = np.pi - rad_alpha - rad_beta

    twoR = side_c / math.sin(rad_gamma)

    side_b = twoR * math.sin(rad_beta)


    # object position with respect to Point A (left eye)
    object_x_wrtA = side_b * math.cos(rad_alpha)
    object_y_wrtA = side_b * math.sin(rad_alpha)

    # object position with respect to gantry center G
    object_x_wrtG = -half_side_c + object_x_wrtA
    object_y_wrtG = object_y_wrtA

    p = Point(object_x_wrtG, object_y_wrtG)

    dis = math.hypot(object_x_wrtG, object_y_wrtG)
    # print(round(dis), "in")

    return p






def triangulate_pos_and_rad_from_goalposts(cs_left, cs_right, prev_pos, prev_rad) -> tuple[Point, float]:
    '''try to determine the robot's position with respect to the fixed goalposts'''


    # if unable to triangulate, return the previous values
    return prev_pos, prev_rad