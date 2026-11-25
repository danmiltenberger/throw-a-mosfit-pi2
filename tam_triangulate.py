import numpy as np
import math
from tam_classes import Point, CameraState, Settings
from tam_topdown import calc_angle_from_screen_center, convert_angle_from_screen_center_to_ccw_east
from dataclasses import field, dataclass
from tam_points import GOALPOST_NORTHEAST, GOALPOST_NORTHWEST, GOALPOST_SOUTHEAST, GOALPOST_SOUTHWEST, FIELD_GOALBOX_CENTER_BOTTOM

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


def triangulate_object_wrt_bot(pos_px_left : Point, pos_px_right : Point) -> tuple[float,float]:
    '''return the distance in inches and angle in radians (+ccw east) of an object wrt the bot'''

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


    dis = math.hypot(object_x_wrtG, object_y_wrtG)
    rad = math.atan(object_y_wrtG / object_x_wrtG)

    return dis, rad


# keys
GREEN_UP = "GREEN_UP"
GREEN_DW = "GREEN_DW"
PURPL_UP = "PURPL_UP"
PURPL_DW = "PURPL_DW"

KNOWN_POINT = "KNOWN_POINT"
DIS_IN = "DIS_IN"
RAD = "RAD"



def get_goalpost_dict(cs_left : CameraState, cs_right: CameraState, is_facing_north : bool, west_is_green : bool = True) -> dict:
    '''go through the 4 possible goalposts and return their distance from bot, angle from bot's east +ccw, and known point on the field'''



    goalposts_dict = {
        GREEN_UP : {},
        GREEN_DW : {},
        PURPL_UP : {},
        PURPL_DW : {},
    }

    if is_facing_north:
        west_goalpost = GOALPOST_NORTHWEST
        east_goalpost = GOALPOST_NORTHEAST
    else:
        west_goalpost = GOALPOST_SOUTHWEST
        east_goalpost = GOALPOST_SOUTHEAST

    if west_is_green:
        goalposts_dict[GREEN_UP][KNOWN_POINT] = west_goalpost
        goalposts_dict[GREEN_DW][KNOWN_POINT] = west_goalpost
        goalposts_dict[PURPL_UP][KNOWN_POINT] = east_goalpost
        goalposts_dict[PURPL_DW][KNOWN_POINT] = east_goalpost
    else:
        goalposts_dict[GREEN_UP][KNOWN_POINT] = east_goalpost
        goalposts_dict[GREEN_DW][KNOWN_POINT] = east_goalpost
        goalposts_dict[PURPL_UP][KNOWN_POINT] = west_goalpost
        goalposts_dict[PURPL_DW][KNOWN_POINT] = west_goalpost

    # green top
    if cs_left.gp_green_up_in_frame and cs_right.gp_green_up_in_frame:
        goalpost_left = cs_left.gp_green_up_pos_px
        goalpost_right = cs_right.gp_green_up_pos_px
        dis, ang = triangulate_object_wrt_bot(goalpost_left, goalpost_right)
        goalposts_dict[GREEN_UP][DIS_IN] = dis
        goalposts_dict[GREEN_UP][RAD] = ang

    # green bottom
    if cs_left.gp_green_dw_in_frame and cs_right.gp_green_dw_in_frame:
        goalpost_left = cs_left.gp_green_dw_pos_px
        goalpost_right = cs_right.gp_green_dw_pos_px
        dis, ang = triangulate_object_wrt_bot(goalpost_left, goalpost_right)
        goalposts_dict[GREEN_DW][DIS_IN] = dis
        goalposts_dict[GREEN_DW][RAD] = ang

    # purple top
    if cs_left.gp_purpl_up_in_frame and cs_right.gp_purpl_up_in_frame:
        goalpost_left = cs_left.gp_purpl_up_pos_px
        goalpost_right = cs_right.gp_purpl_up_pos_px
        dis, ang = triangulate_object_wrt_bot(goalpost_left, goalpost_right)
        goalposts_dict[PURPL_UP][DIS_IN] = dis
        goalposts_dict[PURPL_UP][RAD] = ang    

    # purple bottom
    if cs_left.gp_purpl_dw_in_frame and cs_right.gp_purpl_dw_in_frame:
        goalpost_left = cs_left.gp_purpl_dw_pos_px
        goalpost_right = cs_right.gp_purpl_dw_pos_px
        dis, ang = triangulate_object_wrt_bot(goalpost_left, goalpost_right)
        goalposts_dict[PURPL_DW][DIS_IN] = dis
        goalposts_dict[PURPL_DW][RAD] = ang    

    return goalposts_dict


def print_dict(d : dict):
    for key in d.keys():
        print(key, d[key])
