from tam_constants import SCREEN_CENTER_X
from tam_classes import Point
import math

FOCAL_LENGTH = 1253.333     # recalc this when able


def calc_distance_from_bot(known_width_in: float, percieved_width_px) -> float:

    Z = (known_width_in * FOCAL_LENGTH) / percieved_width_px
    return Z


def calc_focal_length():

    # training from 6ft_center_blue.png
    percieved_width_px = 115
    known_width_in = 7      # FIXME


    focal_length : float = 0



    print(f"updated focal length: {round(focal_length,3)}")


def calc_angle_from_screen_center(point: Point) -> float:

    pixel_x = point.x
    delta_x = pixel_x - SCREEN_CENTER_X

    return -math.atan2(delta_x, FOCAL_LENGTH)


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


def robot_pos_from_object(
    object_pos: Point,
    robot_bearing_rad: float,
    object_dis: float,
    object_bearing_rad: float,
) -> Point:
    """Calculate the robot's field position from a fixed object's position.

    object_pos is the object's known position in the field frame.
    robot_bearing_rad is the robot's known heading, measured
        counter-clockwise from the field's +x axis.
    object_dis is the measured distance from the robot to the object.
    object_bearing_rad is positive to the robot's right, negative left.

    Field +y is up-field; +x is field-right.
    """
    field_bearing_rad = robot_bearing_rad - object_bearing_rad

    return Point(
        x=object_pos.x - object_dis * math.cos(field_bearing_rad),
        y=object_pos.y - object_dis * math.sin(field_bearing_rad),
    )


def robot_pose_from_objects(
    object1_pos: Point,
    object1_dis: float,
    object1_bearing_rad: float,
    object2_pos: Point,
    object2_dis: float,
    object2_bearing_rad: float,
) -> tuple[Point, float]:
    """Calculate robot position and heading from two fixed objects.

    Both observations must correspond to the same robot pose.

    Object positions are known field coordinates.
    Object bearings are positive right, negative left of robot forward.
    Robot heading is counter-clockwise from field +x.

    Returns:
        (robot_pos, robot_bearing_rad)
        Heading is normalized to [-pi, pi).

    With noisy observations, returns the equal-weight least-squares
    rigid alignment of the two observed points to their field positions.
    """
    values = (
        object1_pos.x, object1_pos.y,
        object2_pos.x, object2_pos.y,
        object1_dis, object2_dis,
        object1_bearing_rad, object2_bearing_rad,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("All coordinates and measurements must be finite.")

    if object1_dis <= 0 or object2_dis <= 0:
        raise ValueError("Object distances must be positive.")

    # Local frame: +x forward, +y left.
    local1_x = object1_dis * math.cos(object1_bearing_rad)
    local1_y = -object1_dis * math.sin(object1_bearing_rad)
    local2_x = object2_dis * math.cos(object2_bearing_rad)
    local2_y = -object2_dis * math.sin(object2_bearing_rad)

    field_dx = object2_pos.x - object1_pos.x
    field_dy = object2_pos.y - object1_pos.y
    local_dx = local2_x - local1_x
    local_dy = local2_y - local1_y

    if math.hypot(field_dx, field_dy) <= 1e-9:
        raise ValueError("The two fixed objects must have distinct positions.")

    if math.hypot(local_dx, local_dy) <= 1e-9:
        raise ValueError("The observations must identify distinct local points.")

    robot_bearing_rad = (
        math.atan2(field_dy, field_dx)
        - math.atan2(local_dy, local_dx)
    )
    robot_bearing_rad = (
        (robot_bearing_rad + math.pi) % (2 * math.pi) - math.pi
    )

    cos_heading = math.cos(robot_bearing_rad)
    sin_heading = math.sin(robot_bearing_rad)

    local_mid_x = (local1_x + local2_x) / 2
    local_mid_y = (local1_y + local2_y) / 2
    field_mid_x = (object1_pos.x + object2_pos.x) / 2
    field_mid_y = (object1_pos.y + object2_pos.y) / 2

    robot_pos = Point(
        x=field_mid_x - (
            cos_heading * local_mid_x - sin_heading * local_mid_y
        ),
        y=field_mid_y - (
            sin_heading * local_mid_x + cos_heading * local_mid_y
        ),
    )

    return robot_pos, robot_bearing_rad