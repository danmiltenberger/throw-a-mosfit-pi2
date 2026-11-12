from tam_constants import SCREEN_CENTER_X, CAMERA_CAPTURE_X
from tam_classes import Point, Detection
import math
import numpy as np
import random

FOCAL_LENGTH = 1253.333     # recalc this when able


def calc_distance_from_bot(known_width_in: float, percieved_width_px) -> float:
    '''calculate the distance to an object using the known width and percieved width. Not as good as two sightings but better than nothing'''

    try:
        Z = (known_width_in * FOCAL_LENGTH) / percieved_width_px
    except ZeroDivisionError:
        Z = np.inf

    # no sightings should be further than 140 inches since the field is 12ft = 144 in long
    if Z > 140:
        Z = 140



    return Z


def calc_focal_length():

    # training from 6ft_center_blue.png
    percieved_width_px = 115
    known_width_in = 7      # FIXME


    focal_length : float = 0



    print(f"updated focal length: {round(focal_length,3)}")


def calc_angle_from_screen_center(point: Point) -> float:
    """Return horizontal angle in radians relative to the camera's center.

    Assumes a 62.2-degree horizontal field of view.
    Negative angles are left of center; positive angles are right.
    """
    if CAMERA_CAPTURE_X <= 0:
        raise ValueError("CAMERA_CAPTURE_X must be positive.")

    center_x = CAMERA_CAPTURE_X / 2.0
    half_fov_rad = math.radians(62.2 / 2.0)

    focal_length_px = center_x / math.tan(half_fov_rad)
    offset_x = point.x - center_x

    return math.atan2(offset_x, focal_length_px)


def convert_angle_from_screen_center_to_ccw_east(angle_rad: float) -> float:
    '''convert a radian measure from "North" with northwest as negative and northeast as positive, to a measure ccw from the east +x axis'''
    north_as_rad = np.pi / 2

    from_east_as_rad = north_as_rad - angle_rad

    return from_east_as_rad


import math


def calc_range_and_bearing_with_two_sightings(rad_left: float, rad_right: float, dis_cam_center_to_center_in:float = 5) -> tuple[float,float]:
    """Return horizontal-plane range in inches and bearing in radians from the cameras' midpoint.

    Inputs are angles in radians measured from a shared forward direction:
    negative points left; positive points right.

    Does NOT raise errors (stopping the program), just returns 0,0 if there are errors

    Assumes cameras are X inches apart with parallel forward axes.
    Returns the range in inches and the angle in radians to the object wrt the center of the camera line

    Makes sure that no sighting is further than 140 inches away (long side of the arena is 12ft = 144in)

    """
    for angle in (rad_left, rad_right):
        if not math.isfinite(angle) or not -math.pi / 2 < angle < math.pi / 2:
            
            return 0.0, 0.0
            #raise ValueError("Angles must be finite and between -pi/2 and pi/2.")

    tan_left = math.tan(rad_left)
    tan_right = math.tan(rad_right)
    disparity = tan_left - tan_right

    if disparity <= 0:
        # raise ValueError(
        #     "Sightings must converge ahead of the cameras; "
        #     "rad_left must be greater than rad_right."
        # )

        return 0.0 , 0.0

    forward_in = dis_cam_center_to_center_in / disparity
    sideways_in = forward_in * (tan_left + tan_right) / (2)

    dis_in = math.hypot(sideways_in, forward_in)
    bearing_rad = math.atan2(sideways_in, forward_in)

    if dis_in > 140:
        dis_in = 140

    return dis_in, bearing_rad








def convert_to_field(
    robot_pos: Point,
    robot_bearing_rad: float,
    object_dis: float,
    object_bearing_rad: float,
) -> Point:
    """Convert an object detected in the robot's frame to the field frame.

    Object bearing is positive to the robot's right, negative to its left.
    Field +y is up-field; +x is field-right.
    Robot bearing is measured counter-clockwise from the field's +x axis.
    """
    field_bearing_rad = robot_bearing_rad - object_bearing_rad

    object_pos = Point(
        x=robot_pos.x + object_dis * math.cos(field_bearing_rad),
        y=robot_pos.y + object_dis * math.sin(field_bearing_rad),
    )

    return object_pos

