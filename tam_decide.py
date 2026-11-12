import random
import numpy as np
import math
import time
from typing import Literal
from tam_classes import (
    Point,
    Line,
    FieldState,
    BotCommand,
    get_capture_zone_point,
    Detection,
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


def get_init_fieldstate() -> FieldState:
    fieldstate = FieldState()

    fieldstate.our_bot_pos_in = FIELD_GOALBOX_CENTER_BOTTOM
    fieldstate.our_bot_bearing_rad = BEARING_NORTH

    fieldstate.their_bot_pos_in = FIELD_GOAL_CENTER_TOP
    fieldstate.their_bot_bearing_rad = BEARING_SOUTH

    fieldstate.ball_pos_in = FIELD_CENTER

    return fieldstate


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


def get_bot_command_straight_line(
    fieldstate: FieldState, end_pos: Point, dur_max_sec: float = 2
) -> BotCommand:
    """
    return a command to rotate to point at the end position OR
    return a command to drive to that point"""

    bot_command = BotCommand()

    delta_y = fieldstate.our_bot_pos_in.y - end_pos.y
    delta_x = fieldstate.our_bot_pos_in.y - end_pos.y

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
                fieldstate=fieldstate, end_pos=FIELD_GOALBOX_CENTER_TOP
            )
            status = "moving ball closer to their goal"
            fieldstate.our_bot_target_pos = FIELD_GOALBOX_CENTER_TOP

    # if they have the ball
    if fieldstate.ball_is_theirs:

        # move to our goal to block
        this_command = get_bot_command_straight_line(
            fieldstate=fieldstate, end_pos=FIELD_GOALBOX_CENTER_BOTTOM
        )
        status = "moving to our goal to defend"

        fieldstate.our_bot_target_pos = FIELD_GOALBOX_CENTER_BOTTOM

    # if neither have the ball
    if (fieldstate.ball_is_ours == False) and (fieldstate.ball_is_theirs == False):

        # if we see the ball, move to it
        if fieldstate.ball_is_seen:
            this_command = get_bot_command_straight_line(
                fieldstate=fieldstate, end_pos=fieldstate.ball_pos_in
            )
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


def determine_ball_ownership(fieldstate: FieldState):
    """update the fieldstate with the ball_is_ours / ball_is_theirs True or False's"""

    # TODO

    # if the ball has been moving at reasonably the same speed and direction as opponent bot, assume they have it

    # if we have the limit switch activate, that is a clear confirmation that we have it

    # if the ball is within our code defined capture zone, we should consider it ours
    fieldstate = get_capture_zone_point(fieldstate)

    if is_within_circ(
        point_in_q=fieldstate.ball_pos_in,
        circle_center=fieldstate.capture_zone_center,
        cicle_rad=fieldstate.our_bot_capture_zone_radius,
    ):

        fieldstate.ball_is_ours = True

        return fieldstate

    if fieldstate.ball_is_ours:
        fieldstate.ball_pos_in = fieldstate.capture_zone_center

    # elif
    # TODO check if within opponent's capture zone

    else:
        fieldstate.ball_is_ours = False

    return fieldstate


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


def determine_goalpost_position(fieldstate: FieldState) -> Point | None:
    """by considering our position and direction, determine if the goalpost in frame is Northeast, Northwest, Southeast, or Southwest"""

    # if we see neither goal then there is nothing to be done
    if (fieldstate.goalpost_green_is_seen == False) and (
        fieldstate.goalpost_purple_is_seen == False
    ):
        return None

    # otherwise let's determine if we are facing north towards their goal or south towards our goal (our goal is ALWAYS south)
    bot_is_facing_north: bool = False

    if 0 <= fieldstate.our_bot_bearing_rad <= np.pi:
        bot_is_facing_north = True

    if bot_is_facing_north:

        # if we are facing north and see a purple goalpost
        if fieldstate.goalpost_purple_is_seen:

            # if we know that the purple goalpost should be on the west, it's the northwest goalpost
            if fieldstate.our_west_goalpost == PURPLE:
                return GOALPOST_NORTHWEST

            # otherwise it's the Northeast
            else:
                return GOALPOST_NORTHEAST

        # if we are facing north and see a green goalpost
        elif fieldstate.goalpost_green_is_seen:

            # if we know that the green goalpost should be on the west, it's the northwest goalpost
            if fieldstate.our_west_goalpost == GREEN:
                return GOALPOST_NORTHWEST

            else:
                return GOALPOST_SOUTHEAST

    else:
        # if we are facing SOUTH and see a purple goalpost
        if fieldstate.goalpost_purple_is_seen:

            # if we know that the purple goalpost should be on the west, it's the southwest
            if fieldstate.our_west_goalpost == PURPLE:
                return GOALPOST_SOUTHWEST

            else:
                return GOALPOST_SOUTHEAST

        if fieldstate.goalpost_green_is_seen:
            if fieldstate.our_west_goalpost == GREEN:
                return GOALPOST_SOUTHWEST
            else:
                return GOALPOST_SOUTHEAST


def try_to_update_robot_pos_from_goalposts(
    goalpost_green: Detection, goalpost_purple: Detection, fieldstate: FieldState
) -> FieldState:
    """see if a green and/or purple goalpost is in range. Then, determine what known goalpost position those goalposts should be. Then update robot position"""

    if goalpost_green.in_frame:
        fieldstate.goalpost_green_is_seen = True
        goalpost_detection = goalpost_green

    elif goalpost_purple.in_frame:
        fieldstate.goalpost_purple_is_seen = True
        goalpost_detection = goalpost_purple
    else:
        # if neither are in frame there's nothing to do
        return fieldstate

    # if one of them is in frame, determine it's field position by referencing the robot's view and known field setting
    goalpost_position = determine_goalpost_position(fieldstate)

    # if the function was unable to determine the position, do not update
    if goalpost_position is None:
        return fieldstate

    # # update our robot's position
    # fieldstate.our_bot_pos_in = robot_pos_from_object(
    #     object_bearing_rad= goalpost_detection.ang_from_bot_rad,
    #     object_dis= goalpost_detection.dis_from_bot_in,
    #     object_pos= goalpost_position,
    #     robot_bearing_rad= fieldstate.our_bot_bearing_rad
    # )

    return fieldstate


def convert_detect_list_to_fieldstate(
    detect_list: list[Detection], prev_fieldstate: FieldState | None = None
) -> FieldState:
    """from the list of detected objects, update the fieldstate dataclass"""

    detect_dict = get_detection_dict(detect_list)

    fieldstate = convert_detect_dict_to_fieldstate(
        detect_dict, prev_fieldstate=prev_fieldstate
    )
    return fieldstate


def convert_detect_dict_to_fieldstate(
    detect_dict: dict[str, Detection], prev_fieldstate: FieldState | None = None
) -> FieldState:

    # create a new default or use the previous state
    if prev_fieldstate is None:
        fieldstate = FieldState()
    else:
        fieldstate = prev_fieldstate

    # now unpack them to be more easily worked with
    goalpost_green: Detection = detect_dict[HAT_GREEN]
    goalpost_purpl: Detection = detect_dict[HAT_FUCHSIA]
    bot_yellow: Detection = detect_dict[HAT_YELLOW]
    bot_blue: Detection = detect_dict[HAT_BLUE]
    ball_red: Detection = detect_dict[BALL_RED]

    # if we see a goalpost, try to update the robot position wrt the goalpost
    fieldstate = update_bot_position_from_goalposts(
        fieldstate, goalpost_green, goalpost_purpl
    )

    # try to add the ball to the state, otherwise it stays the same as previous state
    if ball_red.in_frame:

        fieldstate.ball_is_seen = True

        fieldstate.ball_pos_in = convert_to_field(
            object_bearing_rad=ball_red.ang_from_bot_rad,
            object_dis=ball_red.dis_from_bot_in,
            robot_bearing_rad=fieldstate.our_bot_bearing_rad,
            robot_pos=fieldstate.our_bot_pos_in,
        )

    # try to add our opponent to the frame
    if fieldstate.our_team_color == BLUE:
        if bot_yellow.in_frame:

            fieldstate.their_bot_is_seen = True

            fieldstate.their_bot_pos_in = convert_to_field(
                object_bearing_rad=bot_yellow.ang_from_bot_rad,
                object_dis=bot_yellow.dis_from_bot_in,
                robot_bearing_rad=fieldstate.our_bot_bearing_rad,
                robot_pos=fieldstate.our_bot_pos_in,
            )

    if fieldstate.our_team_color == YELLOW:
        if bot_blue.in_frame:
            fieldstate.their_bot_is_seen = True

            fieldstate.their_bot_pos_in = convert_to_field(
                object_bearing_rad=bot_blue.ang_from_bot_rad,
                object_dis=bot_blue.dis_from_bot_in,
                robot_bearing_rad=fieldstate.our_bot_bearing_rad,
                robot_pos=fieldstate.our_bot_pos_in,
            )

    return fieldstate


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


def update_bot_position_from_goalposts(
    fieldstate: FieldState, detection_green: Detection, detection_purple
) -> FieldState:
    """
    Update the robot's position by comparing the distance and range to two known points on the field
    """

    # determine our bearing
    if math.cos(fieldstate.our_bot_bearing_rad) >= 0:
        facing_north = True
    else:
        facing_north = False

    # if we are facing north
    if facing_north:
        left_goalpost = GOALPOST_NORTHWEST

        # if the west is green
        if fieldstate.our_west_goalpost == GREEN:
            detect_left = detection_green
            detect_right = detection_purple


        # if the west is purple
        else:
            detect_left = detection_purple
            detect_right = detection_green

    # if we are facing south
    else:

        left_goalpost = GOALPOST_SOUTHEAST

        if fieldstate.our_west_goalpost == GREEN:
            detect_left = detection_purple
            detect_right = detection_green
        else:
            detect_left = detection_green
            detect_right = detection_purple

    fieldstate.our_bot_pos_in = solve_bot_from_goalpost(
        left_post_pos_in= left_goalpost,
        right_post_dis_in= detect_right.dis_from_bot_in,
        left_post_dis_in= detect_left.dis_from_bot_in,
        facing_north= facing_north,
        prev_pos= fieldstate.our_bot_pos_in
    )


    return fieldstate


def get_detection_lines(detection: Detection) -> list[str]:
    """specify what information to print next to the detection"""

    lines = [
        str(detection.name),
        f"{round(detection.dis_from_bot_in,1)} in",
        f"{round(math.degrees(detection.ang_from_bot_rad),1)}deg",
    ]

    return lines


def try_to_merge_detections(
    detect_left: Detection, detect_right: Detection
) -> Detection:
    """try to find the range from two detections. If unable, flip a coin and return the left or right detection"""

    if detect_left.in_frame and detect_right.in_frame:
        dis_in, bearing_rad = calc_range_and_bearing_with_two_sightings(
            detect_left.ang_from_bot_rad, detect_right.ang_from_bot_rad
        )

        # if the function wasn't able to do range finding (aka returning 0,0), flip a coin and return a detection
        if (dis_in == 0) and (bearing_rad == 0):
            # print("unable to merge in calc_range, flipping coin")
            if random.choice([0, 1]) == 0:
                return detect_left
            else:
                return detect_right

        # otherwise, update inifo and return a detection
        else:
            # copy the left's info but overwrite other info
            merged_detect = detect_left
            merged_detect.name = detect_left.name
            merged_detect.dis_from_bot_in = dis_in
            merged_detect.ang_from_bot_rad = bearing_rad

            # print("merged detections")
            return merged_detect

    # if only one detection is in frame, return that one
    elif detect_left.in_frame:
        # print("unable to merge, only left in frame, returning left")
        return detect_left
    elif detect_right.in_frame:
        # print("unable to merge, only right in frame, returning right")
        return detect_right

    # if neither are in frame, return the left just so the program keeps going
    else:
        # print("unable to merge, neither in frame, returning left")
        detect_left.in_frame = False
        return detect_left


def get_detection_dict(list_detections: list[Detection]) -> dict[str, Detection]:
    """convert the list of detections to a dict of name : Detection"""
    return_dict = {}
    for detection in list_detections:
        return_dict[detection.name] = detection

    return return_dict


def merge_list_detections(
    list_detect_left: list[Detection], list_detect_right: list[Detection]
) -> dict[str, Detection]:
    """go through the detect list and merge if possible, or pick the one that is in frame otherwise"""

    search_list = [BALL_RED, HAT_BLUE, HAT_FUCHSIA, HAT_GREEN, HAT_YELLOW]

    def merge_detect_by_name(
        name: str, dict_detect_merged: dict[str, Detection]
    ) -> dict[str, Detection]:
        detect_left = dict_detect_left[name]
        detect_right = dict_detect_right[name]
        dict_detect_merged[name] = try_to_merge_detections(detect_left, detect_right)
        return dict_detect_merged

    dict_detect_left = get_detection_dict(list_detect_left)
    dict_detect_right = get_detection_dict(list_detect_right)

    # default to the left dict, update below
    dict_detect_merged = dict_detect_left

    # go through each and try to merge by name
    for detect_name in search_list:
        dict_detect_merged = merge_detect_by_name(detect_name, dict_detect_merged)

    return dict_detect_merged


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