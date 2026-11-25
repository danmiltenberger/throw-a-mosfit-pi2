from tam_constants import SCREEN_CENTER_X, CAMERA_CAPTURE_X
from tam_classes import Point, Detection
from tam_points import GOALPOST_NORTHEAST, GOALPOST_NORTHWEST, GOALPOST_SOUTHEAST, GOALPOST_SOUTHWEST
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


def calc_range_and_bearing_with_two_sightings(rad_left: float, rad_right: float, dis_cam_center_to_center_in:float = 5) -> tuple[float,float]:
    """Return horizontal-plane range in inches and bearing in radians from the cameras' midpoint.

    Inputs are angles in radians measured from a shared forward direction:
    negative points left; positive points right.

    Does NOT raise errors (stopping the program), just returns 0,0 if there are errors

    Assumes cameras are X inches apart with parallel forward axes.
    Returns the range in inches and the angle in radians to the object wrt the center of the camera line

    Makes sure that no sighting is further than 144 inches away (long side of the arena is 12ft = 144in)

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

    if dis_in > 144:
        dis_in = 144

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
    field_bearing_rad = robot_bearing_rad - object_bearing_rad + np.pi/2

    object_pos = Point(
        x=robot_pos.x + object_dis * math.cos(field_bearing_rad),
        y=robot_pos.y + object_dis * math.sin(field_bearing_rad),
    )

    return object_pos


def law_of_sines(
        solve_for : str,
        side_a : float | None = None,
        side_b : float | None = None,
        side_c : float | None = None,
        rad_alpha : float | None = None,
        rad_beta : float | None = None,
        rad_gamma : float | None = None,

) -> float:
    '''solve a triangle using law of sines
    solve for side_a, side_b, side_c, rad_alpha, rad_beta, or rad_gamma

    Note: when solving for an angle from sides, asin() only returns the
    acute solution (the SSA "ambiguous case" may also have an obtuse one).
    '''

    sides = {"a": side_a, "b": side_b, "c": side_c}
    angles = {"a": rad_alpha, "b": rad_beta, "c": rad_gamma}

    names = {
        "side_a": ("side", "a"), "side_b": ("side", "b"), "side_c": ("side", "c"),
        "rad_alpha": ("angle", "a"), "rad_beta": ("angle", "b"), "rad_gamma": ("angle", "c"),
    }
    if solve_for not in names:
        raise ValueError(f"unknown solve_for {solve_for!r}, expected one of {list(names)}")

    kind, target = names[solve_for]

    # if exactly two angles are known, the third is pi minus their sum
    known = [v for v in angles.values() if v is not None]
    if len(known) == 2:
        missing = next(k for k, v in angles.items() if v is None)
        third_angle = math.pi - sum(known)   # plain float
        angles[missing] = third_angle
        if kind == "angle" and missing == target:
            return third_angle

    # the target's own value is what we're solving for, so don't use it
    if kind == "side":
        sides[target] = None
    else:
        angles[target] = None

    # find a known side / opposite angle pair to get the ratio side / sin(angle)
    ratio = None
    for k in "abc":
        s, ang = sides[k], angles[k]
        if s is not None and ang is not None:
            ratio = s / math.sin(ang)
            break

    if ratio is None:
        raise ValueError(
            f"unable to solve for {solve_for}: need a known side and its opposite angle"
        )

    if kind == "side":
        target_angle = angles[target]
        if target_angle is None:
            raise ValueError(f"unable to solve for {solve_for}: need the opposite angle")
        return ratio * math.sin(target_angle)

    target_side = sides[target]
    if target_side is None:
        raise ValueError(f"unable to solve for {solve_for}: need side_{target}")
    x = target_side / ratio
    if not -1 <= x <= 1:
        raise ValueError("no valid triangle: sine value out of range")
    return math.asin(x)


def fix_asa_alpha_beta(rad_L: float, rad_R: float) -> tuple[float, float]:
    '''convert camera angles (from forward, positive = right) into the
    internal angles of the triangle L-R-target.
    alpha is at L, beta is at R.
    '''
    rad_alpha = np.pi / 2 - rad_L
    rad_beta = np.pi / 2 + rad_R

    # rays must converge in front of the cameras
    if rad_alpha <= 0 or rad_beta <= 0 or rad_alpha + rad_beta >= np.pi:
        raise ValueError("rays do not converge in front of the gantry")
    return rad_alpha, rad_beta

def _target_in_robot_frame(
        rad_L: float, rad_R: float, line_LR_in: float) -> tuple[float, float]:
    '''position of a target in the robot frame:
    origin at the midpoint of LR, +x to the right, +y forward'''
    rad_alpha, rad_beta = fix_asa_alpha_beta(rad_L, rad_R)
    line_L_in = law_of_sines(
        side_a=None, side_b=None, side_c=line_LR_in,
        rad_alpha=rad_alpha, rad_beta=rad_beta, rad_gamma=None,
        solve_for="side_b",
    )
    x = -line_LR_in / 2 + line_L_in * np.sin(rad_L)
    y = line_L_in * np.cos(rad_L)
    return x, y


def _rotate(x: float, y: float, psi: float) -> tuple[float, float]:
    return (x * np.cos(psi) - y * np.sin(psi),
            x * np.sin(psi) + y * np.cos(psi))


def calc_pos_and_angle_from_goalposts(
        rad_LW: float | None,
        rad_LE: float | None,
        rad_RW: float | None,
        rad_RE: float | None,
        rad_BOT: float,
        pos_BOT: Point,
        facing_north: bool = True,
        line_LR_in=5,
) -> tuple[Point, float]:
    if facing_north:
        west_goalpost = GOALPOST_NORTHWEST
        east_goalpost = GOALPOST_NORTHEAST
    else:
        west_goalpost = GOALPOST_SOUTHWEST
        east_goalpost = GOALPOST_SOUTHEAST

    # (position in robot frame, position in world frame) for each visible post
    seen = []
    for rad_L, rad_R, post in [
        (rad_LW, rad_RW, west_goalpost),
        (rad_LE, rad_RE, east_goalpost),
    ]:
        if rad_L is None or rad_R is None:
            continue
        try:
            seen.append((_target_in_robot_frame(rad_L, rad_R, line_LR_in), post))
        except ValueError:
            continue  # bad geometry, ignore this post

    if len(seen) == 2:
        # two posts: the rigid transform robot->world is fully determined
        (w, W), (e, E) = seen
        psi = (np.arctan2(E.y - W.y, E.x - W.x)
               - np.arctan2(e[1] - w[1], e[0] - w[0]))
    elif len(seen) == 1:
        # one post: fall back on the prior heading
        psi = -rad_BOT
    else:
        # unable to do any rangefinding
        return pos_BOT, rad_BOT

    (rx, ry), post = seen[0]
    dx, dy = _rotate(rx, ry, psi)
    new_pos = Point(post.x - dx, post.y - dy)
    new_heading = float(np.arctan2(np.sin(-psi), np.cos(-psi)))  # wrap to (-pi, pi]
    return new_pos, new_heading
        
