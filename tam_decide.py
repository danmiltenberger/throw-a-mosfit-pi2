import random
import numpy as np
import math
import time
from typing import Literal
from tam_classes import (
    Point,
    Line,
    FieldState,
    Detection,
    CameraState
)
from tam_commands import *
from tam_ourbot import *
from tam_points import *
from tam_colors import PURPLE, GREEN, BLUE, YELLOW
from tam_topdown import convert_to_field, calc_range_and_bearing_with_two_sightings
from tam_constants import (
    HAT_BLUE,
    HAT_FUCHSIA,
    HAT_GREEN,
    HAT_YELLOW,
    BALL_RED,
    BEARING_NORTH,
    BEARING_SOUTH,
)


def get_init_fieldstate(is_penalty_kick: bool = False) -> FieldState:
    fieldstate = FieldState()

    fieldstate.our_bot_pos_in = FIELD_GOALBOX_CENTER_BOTTOM
    fieldstate.our_bot_bearing_rad = BEARING_NORTH

    if not is_penalty_kick:
        fieldstate.their_bot_pos_in = FIELD_GOAL_CENTER_TOP
        fieldstate.their_bot_bearing_rad = BEARING_SOUTH

    fieldstate.ball_pos_in = FIELD_CENTER

    return fieldstate


def is_on_line(point_in_q: Point, line: Line, tol_in: float = 1.0) -> bool:
    """True if point_in_q is within tol_in of the SEGMENT from line.pt1 to line.pt2."""
    dx = line.pt2.x - line.pt1.x
    dy = line.pt2.y - line.pt1.y
    seg_len = math.hypot(dx, dy)
    if seg_len < 1e-9:  # degenerate line: just check distance to the point
        return math.hypot(point_in_q.x - line.pt1.x, point_in_q.y - line.pt1.y) < tol_in
    ux, uy = dx / seg_len, dy / seg_len

    rx = point_in_q.x - line.pt1.x
    ry = point_in_q.y - line.pt1.y

    along = rx * ux + ry * uy            # distance along the segment from pt1
    if along < 0 or along > seg_len:     # behind pt1 or past pt2
        return False

    off_line = abs(ux * ry - uy * rx)    # true perpendicular distance to the line
    return off_line < tol_in


def perpendicular_line(line: Line, point: Point, length: float = 1.0, side: int = 1) -> Line:
    """Line through `point`, perpendicular to `line`, extending `length` inches.
    side = +1 -> left of line direction (pt1 -> pt2), -1 -> right."""

    dx = line.pt2.x - line.pt1.x
    dy = line.pt2.y - line.pt1.y
    mag = math.hypot(dx, dy)
    if mag < 1e-9:
        raise ValueError("line has zero length")

    # unit perpendicular: rotate the unit direction 90 degrees
    px, py = -dy / mag, dx / mag

    end = Point(point.x + side * length * px, point.y + side * length * py)
    return Line(pt1=point, pt2=end)


def is_within_rect(point_in_q: Point, top_left: Point, bot_right: Point) -> bool:
    # check x

    within_x: bool = False
    within_y: bool = False

    if top_left.x <= point_in_q.x <= bot_right.x:
        within_x = True

    if bot_right.y <= point_in_q.y <= top_left.y:
        within_y = True

    if within_x and within_y:
        return True
    else:
        return False


def is_within_circ(point_in_q: Point, circle_center: Point, cicle_rad: float) -> bool:
    """Return True if the point is inside or on the circle."""
    if cicle_rad < 0:
        raise ValueError("Circle radius must be non-negative.")

    dx = point_in_q.x - circle_center.x
    dy = point_in_q.y - circle_center.y

    return dx * dx + dy * dy <= cicle_rad * cicle_rad


def get_bot_command_straight_line(
    fieldstate: FieldState, end_pos: Point, dur_max_sec: float = 2
) -> BotCommand:
    """
    return a command to rotate to point at the end position OR
    return a command to drive to that point"""

    bot_command = BotCommand()

    delta_y = fieldstate.our_bot_pos_in.y - end_pos.y
    delta_x = fieldstate.our_bot_pos_in.x - end_pos.x

    bot_command = get_turn_command(
        robot_position=fieldstate.our_bot_pos_in,
        target_position=end_pos,
        bearing=fieldstate.our_bot_bearing_rad,
        robot_turn_speed_rad_per_sec=rad_per_sec_rotation,
    )

    # if it's close enough to the angle, drive to it
    if bot_command.dur_sec <= 0.1:
        bot_command.com_str = BOT_FORWARD

        # x = vel*t, so t = x/vel
        dis_to_target = math.hypot(delta_x, delta_y)
        command_duration = dis_to_target / in_per_sec_forward
        bot_command.dur_sec = command_duration

    # double check that it won't take too long to execute the command
    if bot_command.dur_sec > dur_max_sec:
        bot_command.dur_sec = dur_max_sec

    return bot_command



def get_turn_command(
    robot_position: Point,
    target_position: Point,
    bearing: float,
    robot_turn_speed_rad_per_sec: float,
    turn_180_bias: Literal["clockwise", "counterclockwise"] = "clockwise",
) -> BotCommand:
    """Return the shortest turn direction and duration in seconds.

    Args:
        robot_position: Robot's (x, y) coordinates.
        target_position: Target's (x, y) coordinates.
        bearing: Current heading in radians, measured counterclockwise
            from the positive x-axis.
        robot_turn_speed_rad_per_sec: Positive angular speed.
        turn_180_bias: Preferred direction when the target is exactly
            180 degrees from the current bearing.

    Returns:
        ("ROTATE_LEFT" or "ROTATE_RIGHT", duration_seconds).
        A zero-duration turn uses "ROTATE_LEFT".
    """
    x, y = robot_position.x, robot_position.y
    target_x, target_y = target_position.x, target_position.y

    if not all(
        math.isfinite(value)
        for value in (
            x,
            y,
            target_x,
            target_y,
            bearing,
            robot_turn_speed_rad_per_sec,
        )
    ):
        raise ValueError("All numeric inputs must be finite.")

    if robot_turn_speed_rad_per_sec <= 0:
        raise ValueError("robot_turn_speed_rad_per_sec must be positive.")

    if turn_180_bias not in ("clockwise", "counterclockwise"):
        raise ValueError("turn_180_bias must be 'clockwise' or 'counterclockwise'.")

    dx = target_x - x
    dy = target_y - y

    if dx == 0 and dy == 0:

        return BotCommand(BOT_ROTATE_LEFT, dur_sec=0)

    target_bearing = math.atan2(dy, dx)

    # Normalize to [-pi, pi) for the shortest turn.
    turn_angle = (target_bearing - bearing + math.pi) % (2 * math.pi) - math.pi

    # Use a small tolerance to accommodate floating-point rounding.
    if math.isclose(abs(turn_angle), math.pi, rel_tol=0.0, abs_tol=1e-12):
        turn_angle = math.pi if turn_180_bias == "counterclockwise" else -math.pi

    duration = abs(turn_angle) / robot_turn_speed_rad_per_sec
    bot_command = BotCommand(dur_sec=duration)

    if turn_angle >= 0:
        bot_command.com_str = BOT_ROTATE_LEFT
    else:
        bot_command.com_str = BOT_ROTATE_RIGHT

    return bot_command




def is_close_enough_to_goal(pos: Point) -> bool:
    """return True if bot should go for the kick, else False. Consider distance and obstacles"""

    goalbox_north_top_left = GOALPOST_NORTHWEST
    goalbox_north_bot_right = Point(
        x=GOALPOST_NORTHWEST.x + 48,
        y=GOALPOST_NORTHWEST.y - 24,
    )

    # if bot is not within shoot rectangle, don't go for it
    if (
        is_within_rect(
            pos, top_left=goalbox_north_top_left, bot_right=goalbox_north_bot_right
        )
        == False
    ):
        return False

    # TODO add more here about goal shooting considerations
    else:
        return True


def has_N_seconds_passed(time_start: float, N_sec: float) -> bool:
    """has N seconds passed since the time start?"""
    current_time = time.perf_counter()

    if abs(time_start - current_time) >= N_sec:
        return True
    else:
        return False




def solve_bot_from_goalpost(
    left_post_dis_in: float,
    right_post_dis_in: float,
    left_post_pos_in: Point,
    prev_pos : Point,
    facing_north: bool = True,

) -> Point:
    """from the measured distances and the known distance between the posts, determine the position of the bot. If unable, return the previous position"""

    # standard triangle notation, with base c between goal posts, a between left and bot, b between right and bot
    side_c = 48
    side_a = left_post_dis_in
    side_b = right_post_dis_in

    # find the angle from the left goalpost (B) to our bot
    # law of cosines
    try:
        rad_beta = math.acos((side_a**2 + side_c**2 - side_b**2) / (2 * side_a * side_c))
    except:
        return prev_pos

    # find our bot's position wrt left goalpost
    delta_x = side_a * math.cos(rad_beta)
    delta_y = side_a * math.sin(rad_beta)

    if facing_north:
        our_bot_pos_in = Point(
            x=left_post_pos_in.x + delta_x, y=left_post_pos_in.y - delta_y
        )
    else:
        our_bot_pos_in = Point(
            x=left_post_pos_in.x - delta_x, y=left_post_pos_in.y + delta_y
        )

    return our_bot_pos_in




def get_detection_dict(list_detections: list[Detection]) -> dict[str, Detection]:
    """convert the list of detections to a dict of name : Detection"""
    return_dict = {}
    for detection in list_detections:
        return_dict[detection.name] = detection

    return return_dict



def blend_fieldstates(list_fs: list[FieldState], num_to_blend: int = 10) -> FieldState:
    '''from a list of fieldstates, get the average position (since the camera can have things jump around)'''

    # copy the last item in the list (most recent)
    fs_blended = list_fs[-1]

    list_fs_last_n = list_fs[-num_to_blend:]
    num_to_blend = len(list_fs_last_n)
    if num_to_blend == 0:
        raise ValueError("list of fieldstates must include at least one, got 0")


    avg_ball_pos_in_x : float = 0
    avg_ball_pos_in_y : float = 0

    avg_bot_pos_in_x : float = 0
    avg_bot_pos_in_y : float = 0

    avg_their_bot_pos_in_x : float = 0
    avg_their_bot_pos_in_y : float = 0

    for fs in list_fs_last_n:

        # create running tally to then average
        avg_ball_pos_in_x += fs.ball_pos_in.x
        avg_ball_pos_in_y += fs.ball_pos_in.y

        avg_bot_pos_in_x += fs.our_bot_pos_in.x
        avg_bot_pos_in_y += fs.our_bot_pos_in.y

        avg_their_bot_pos_in_x += fs.their_bot_pos_in.x
        avg_their_bot_pos_in_y += fs.their_bot_pos_in.y

    # ball
    avg_ball_pos_in_x = avg_ball_pos_in_x / num_to_blend
    avg_ball_pos_in_y = avg_ball_pos_in_y / num_to_blend
    fs_blended.ball_pos_in = Point(
        x= avg_ball_pos_in_x,
        y= avg_ball_pos_in_y
    )

    # our bot
    avg_bot_pos_in_x = avg_bot_pos_in_x / num_to_blend
    avg_bot_pos_in_y = avg_bot_pos_in_y / num_to_blend
    fs_blended.our_bot_pos_in = Point(
        x= avg_bot_pos_in_x,
        y= avg_bot_pos_in_y
    )

    # their bot
    avg_their_bot_pos_in_x = avg_their_bot_pos_in_x / num_to_blend
    avg_their_bot_pos_in_y = avg_their_bot_pos_in_y / num_to_blend
    fs_blended.their_bot_pos_in = Point(
            x= avg_their_bot_pos_in_x,
            y= avg_their_bot_pos_in_y
        )

    return fs_blended


def get_botcom_from_cam(cs: CameraState, our_goal_is_green_purple: bool = True) -> BotCommand:
    '''get command using just what the camera sees. No fancy top down trig whatever'''

    sec_per_rad = 1 / rad_per_sec_rotation
    sec_per_inch = 1 / in_per_sec_forward

    # default to doing nothing
    bot_command = BotCommand()

    # if we don't see the ball, look for it
    if cs.ball_in_frame == False:
        # turn 45 degrees, for fast programming let's say always always always always turn left.
        
        rad_45 = math.radians(45)
        dur_sec = sec_per_rad * rad_45
        bot_command.com_str = BOT_ROTATE_LEFT
        bot_command.dur_sec = dur_sec

    # if we're more than 100 pixels off from facing it, rotate to the ball
    elif abs(CAMERA_CENTER_X - cs.ball_pos_px.x) > 100: 
        # turn by 10 deg
        rad_10 = math.radians(10)
        bot_command.dur_sec = sec_per_rad * rad_10

        # determine direction
        if CAMERA_CENTER_X - cs.ball_pos_px.x > 0:  # PHOEBE CHANGED "CAPTURE" -> "CENTER"
            bot_command.com_str = BOT_ROTATE_LEFT
        else:
            bot_command.com_str = BOT_ROTATE_RIGHT

    # if we're close enough, drive a little bit toward it
    else:
        # move 12 inches toward the ball
        bot_command.dur_sec = sec_per_inch * 12
        bot_command.com_str = BOT_FORWARD

    # TODO - once we have the ball, go to the goal

    return bot_command


# def is_on_line(point_in_q: Point, line: Line) -> bool:
#     # check if a given point lies on the line between points

#     # equation of line: y = mx + b
#     rise = line.pt2.y - line.pt1.y
#     run = line.pt2.x - line.pt1.x
#     m = rise / run

#     # solve for b (y intercept) using one of the poitns
#     b = line.pt1.y - m * line.pt1.x

#     # check if new point lies along the line
#     calc_y = m * point_in_q.x + b

#     # round to nearest whole num
#     calc_y = round(calc_y)
#     given_y = round(point_in_q.y)

#     if calc_y == given_y:
#         return True
#     else:
#         return False


