
### all the functions that help the robot reach a conclusion
import math
import time
from typing import Literal
from tam_classes import Point, Line, FieldState, BotCommand, get_capture_zone_point
from tam_commands import *
from tam_ourbot import *
from tam_points import *



def is_on_line(point_in_q: Point, line: Line) -> bool:
    # check if a given point lies on the line between points

    # equation of line: y = mx + b
    rise = line.pt2.y - line.pt1.y
    run = line.pt2.x - line.pt1.x
    m = rise / run

    # solve for b (y intercept) using one of the poitns
    b = line.pt1.y - m * line.pt1.x

    # check if new point lies along the line
    calc_y = m * point_in_q.x + b

    # round to nearest whole num
    calc_y = round(calc_y)
    given_y = round(point_in_q.y)

    if calc_y == given_y:
        return True
    else:
        return False


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



def get_bot_command_straight_line(fieldstate: FieldState, end_pos: Point, dur_max_sec : float = 2) -> BotCommand:
    '''
    return a command to rotate to point at the end position OR 
    return a command to drive to that point'''

    bot_command = BotCommand()

    delta_y = fieldstate.our_bot_pos_in.y - end_pos.y
    delta_x = fieldstate.our_bot_pos_in.y - end_pos.y
  
    
    bot_command = get_turn_command(
        robot_position= fieldstate.our_bot_pos_in, 
        target_position= end_pos,
        bearing= fieldstate.our_bot_bearing_rad,
        robot_turn_speed_rad_per_sec= rad_per_sec_rotation
        )

    # if it's close enough to the angle, drive to it
    if bot_command.dur_sec <= 0.1:
        bot_command.com_str = BOT_FORWARD
        
        #x = vel*t, so t = x/vel
        dis_to_target = math.hypot(delta_x, delta_y)
        command_duration = dis_to_target / in_per_sec_forward 
        bot_command.dur_sec = command_duration

    # double check that it won't take too long to execute the command
    if bot_command.dur_sec > dur_max_sec:
        bot_command.dur_sec = dur_max_sec

    return bot_command


def get_bot_command(fieldstate: FieldState) -> tuple[BotCommand, str]:


    # placeholder to then modify
    this_command = BotCommand()

    status = "UNDECIDED"

    # determine who has the ball so we can make decisions
    fieldstate = determine_ball_ownership(fieldstate)

 
    # if we have the ball
    if fieldstate.ball_is_ours:

        # if we are close to the goal, kick
        if is_close_enough_to_goal(fieldstate.our_bot_pos_in):
            this_command.com_str = BOT_KICK
            status = "kicking ball"

            fieldstate.our_bot_target_pos = FIELD_GOAL_CENTER_TOP
            quit("Kicked the ball")

        # otherwise move to their goal
        else:
            this_command = get_bot_command_straight_line(
                fieldstate=fieldstate, 
                end_pos= FIELD_GOALBOX_CENTER_TOP)
            status = "moving ball closer to their goal"
            fieldstate.our_bot_target_pos = FIELD_GOALBOX_CENTER_TOP

    # if they have the ball
    if fieldstate.ball_is_theirs:

        # move to our goal to block
        this_command = get_bot_command_straight_line(fieldstate=fieldstate, end_pos= FIELD_GOALBOX_CENTER_BOTTOM)
        status = "moving to our goal to defend"

        fieldstate.our_bot_target_pos = FIELD_GOALBOX_CENTER_BOTTOM
    

    # if neither have the ball
    if (fieldstate.ball_is_ours == False) and (fieldstate.ball_is_theirs == False):

        # if we see the ball, move to it
        if fieldstate.ball_is_seen:
            this_command = get_bot_command_straight_line(fieldstate=fieldstate, end_pos= fieldstate.ball_pos_in)
            status = "moving to ball"

            fieldstate.our_bot_target_pos = fieldstate.ball_pos_in

        # if we don't, look for it
        else:
            status = "looking for ball"

    return this_command, status


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

    if not all(math.isfinite(value) for value in (
        x, y, target_x, target_y, bearing,
        robot_turn_speed_rad_per_sec,
    )):
        raise ValueError("All numeric inputs must be finite.")

    if robot_turn_speed_rad_per_sec <= 0:
        raise ValueError("robot_turn_speed_rad_per_sec must be positive.")

    if turn_180_bias not in ("clockwise", "counterclockwise"):
        raise ValueError(
            "turn_180_bias must be 'clockwise' or 'counterclockwise'."
        )

    dx = target_x - x
    dy = target_y - y

    if dx == 0 and dy == 0:

        return BotCommand(BOT_ROTATE_LEFT, dur_sec=0)

    target_bearing = math.atan2(dy, dx)

    # Normalize to [-pi, pi) for the shortest turn.
    turn_angle = (
        (target_bearing - bearing + math.pi) % (2 * math.pi)
        - math.pi
    )

    # Use a small tolerance to accommodate floating-point rounding.
    if math.isclose(
        abs(turn_angle), math.pi, rel_tol=0.0, abs_tol=1e-12
    ):
        turn_angle = (
            math.pi if turn_180_bias == "counterclockwise" else -math.pi
        )

    duration = abs(turn_angle) / robot_turn_speed_rad_per_sec
    bot_command = BotCommand(dur_sec= duration)

    if turn_angle >= 0:
        bot_command.com_str = BOT_ROTATE_LEFT
    else:
        bot_command.com_str = BOT_ROTATE_RIGHT


    return bot_command


def determine_ball_ownership(fieldstate: FieldState):
    '''update the fieldstate with the ball_is_ours / ball_is_theirs True or False's'''


    # TODO

    # if the ball has been moving at reasonably the same speed and direction as opponent bot, assume they have it

    # if we have the limit switch activate, that is a clear confirmation that we have it

    # if the ball is within our code defined capture zone, we should consider it ours 
    fieldstate = get_capture_zone_point(fieldstate)

    if is_within_circ(
        point_in_q=fieldstate.ball_pos_in, 
        circle_center=fieldstate.capture_zone_center, 
        cicle_rad=fieldstate.our_bot_capture_zone_radius):

        fieldstate.ball_is_ours = True

        return fieldstate

    if fieldstate.ball_is_ours:
        fieldstate.ball_pos_in = fieldstate.capture_zone_center
    


    #elif 
    # TODO check if within opponent's capture zone

    else:
        fieldstate.ball_is_ours = False

    return fieldstate


def is_close_enough_to_goal(pos: Point) -> bool:
    '''return True if bot should go for the kick, else False. Consider distance and obstacles'''


    goalbox_north_top_left = GOALPOST_NORTHWEST
    goalbox_north_bot_right = Point(
        x= GOALPOST_NORTHWEST.x + 48,
        y= GOALPOST_NORTHWEST.y - 24,
    )

    # if bot is not within shoot rectangle, don't go for it
    if is_within_rect(pos, top_left= goalbox_north_top_left, bot_right= goalbox_north_bot_right) == False:
        return False
   
   
    # TODO add more here about goal shooting considerations
    else:
        return True


def has_N_seconds_passed(time_start: float, N_sec: float) -> bool:
    '''has N seconds passed since the time start?'''
    current_time = time.perf_counter()

    if abs(time_start - current_time) >= N_sec:
        return True
    else:
        return False




