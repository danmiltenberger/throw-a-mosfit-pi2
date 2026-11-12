from dataclasses import dataclass
import numpy as np
import math
from tam_points import GOALPOST_NORTHEAST, GOALPOST_NORTHWEST, GOALPOST_SOUTHEAST, GOALPOST_SOUTHWEST
from tam_classes import Point

@dataclass
class Triangle():
    side_a : float = 0
    side_b : float = 0
    side_c : float = 0
    rad_alpha : float = 0
    rad_beta : float = 0
    rad_gamma : float = 0
    two_r : float = 0


    def __str__(self) -> str:
        return_str = f"Tri: {round(self.side_a,1)}a {round(self.side_b,1)}b, {round(self.side_c,1)}c, "
        return_str += f"{round(math.degrees(self.rad_alpha))}alpha,"
        return_str += f"{round(math.degrees(self.rad_beta))}beta,"
        return_str += f"{round(math.degrees(self.rad_gamma))}gamma deg,"

        return return_str


def solve_tri_asa(rad_alpha: float, side_c : float, rad_beta : float) -> Triangle:
    '''solve an angle-side-angle triangle using law of sines with standard triangle notation'''
    tri = Triangle(
        rad_alpha= rad_alpha,
        rad_beta= rad_beta,
        side_c=side_c
    )

    # solve for missing angle
    rad_gamma = np.pi - rad_alpha - rad_beta
    tri.rad_gamma = rad_gamma

    # solve the ratio
    two_r = side_c / math.sin(rad_gamma)

    # law of sines
    side_a = two_r * math.sin(rad_alpha)
    side_b = two_r * math.sin(rad_beta)

    # package
    tri.side_a = side_a
    tri.side_b = side_b
    tri.two_r = two_r



    return tri


def solve_tri_sss(side_a : float, side_b: float, side_c: float) -> Triangle:
    '''solve a side, side, side triangle
    source: https://en.wikipedia.org/wiki/Law_of_cosines'''

    tri = Triangle(
        side_a= side_a,
        side_b=side_b,
        side_c=side_c
    )

    rad_alpha = math.acos((side_b**2 + side_c**2 - side_a**2)/(2*side_b*side_c))

    rad_gamma = math.acos((side_a**2 + side_b**2 - side_c**2)/(2*side_a*side_b))

    rad_beta = np.pi - rad_alpha - rad_gamma

    tri.rad_alpha = rad_alpha
    tri.rad_beta = rad_beta
    tri.rad_gamma = rad_gamma

    return tri


def get_pos_and_bearing_two_goalposts(
        rad_left_to_east : float,
        rad_left_to_west : float,
        rad_right_to_east : float,
        rad_right_to_west : float,
        is_facing_north: bool = True,
) -> tuple[Point, float]:
    '''from both cameras sighting both goalposts, do the trig to find our position
    all angles must be measured from the bot's 3oclock position with +ccw
    
    '''

    if is_facing_north:
        point_west = GOALPOST_NORTHWEST
        point_east = GOALPOST_NORTHEAST
    else:
        point_west = GOALPOST_SOUTHWEST
        point_east = GOALPOST_SOUTHEAST

    # known distances from point to point
    in_LR = 5
    in_WE = 48


    # solve triangle LRW (both eyes to west goal)
    tri_WEL = solve_tri_asa(
        rad_alpha= rad_left_to_west,
        rad_beta= rad_right_to_west,
        side_c= in_LR
    )

    # solve triangle LRE (both eyes to east goal)
    tri_WER = solve_tri_asa(
        rad_alpha= rad_left_to_east,
        rad_beta= rad_right_to_east,
        side_c= in_LR
    )

    # solve point L using triangle WEL (both goals to left eye)
    #tri_WEL = solve_tri_sss()

    # solve point R using triangle WER (both goals to right eye)
    #tri_WER = solve_tri_sss()

    # find midpoint of line LR using both points

    # find angle from field +x to line LR using both points
 

    # return values to the user
    bot_pos_in = Point(0,0)
    bot_bearing_rad : float = 0


    return bot_pos_in, bot_bearing_rad