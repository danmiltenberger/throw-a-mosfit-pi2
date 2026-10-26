from classes import FieldState, Point
from tam_library_analyze_field import is_within_rect
from tam_library_draw_field import draw_field_from_field_state, get_field_frame
from tam_library import show_frame
from constants import *
from constants_points import *
from constants_rads import *
from variables import *
from variables_robot import *



def main():
    # test these different functions for different states
    fieldstate = FieldState(
        our_bot_pos_in= FIELD_GOALBOX_CENTER_BOTTOM,
        our_bot_bearing_rad= BEARING_NORTH_EAST,
        ball_pos_in= FIELD_CENTER
    )

    pick_best_movement_commands(fieldstate= fieldstate, desired_pos= fieldstate.ball_pos_in)

    field_frame = get_field_frame()
    field_frame = draw_field_from_field_state(field_frame, fieldstate)
    show_frame(field_frame)



def get_command(fieldstate: FieldState) -> str:
    '''analyze the field and determine what actions to take'''

    ## determine who has the ball
    fieldstate = determine_ball_ownership(fieldstate)


    # if we have it, move to their goal to try and score
    if fieldstate.ball_is_ours:

        if is_close_enough_to_goal(fieldstate.ball_pos_in):
            command_kick = get_command_to_kick(fieldstate)
            return command_kick

        command_towards_their_goal = get_command_to_their_goal(fieldstate)

        return command_towards_their_goal

    # if they have it, move to our goal to try and block
    elif fieldstate.ball_is_theirs:

        command_towards_our_goal = get_command_to_our_goal(fieldstate)
        return command_towards_our_goal

    # if we don't know where it is, look for it
    elif (fieldstate.ball_is_ours == False) and (fieldstate.ball_is_theirs == False):
        command_search_for_ball = get_command_search_for_ball(fieldstate)
        return command_search_for_ball

    else:
        print("unable to determine action to take")
        return "NO_COMMAND"


def determine_ball_ownership(fieldstate: FieldState):
    '''update the fieldstate with the ball_is_ours / ball_is_theirs True or False's'''

    # TODO

    # if the ball has been moving at reasonably the same speed and direction as opponent bot, assume they have it

    # if we have the limit switch activate, that is a clear confirmation that we have it

    # also if the ball is within our code defined capture zone, we should consider it ours 
    # with some percentage of uncertainty

    return fieldstate


def get_command_to_their_goal(fieldstate: FieldState) -> str:
    '''determine a forward/backward/strafe/angle etc sequence to move toward their goal'''

    # FIXME
    return BOT_FORWARD


def get_command_to_our_goal(fieldstate: FieldState) -> str:
    '''determine a forward/backward/strafe/angle etc sequence to move toward our goal'''

    # FIXME
    return BOT_BACKWARD


def get_command_search_for_ball(fieldstate: FieldState) -> str:
    '''with a given guess on where bot thinks the ball is, look for ball'''
    return BOT_ROTATE_LEFT


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


def get_command_to_kick(field_state: FieldState):


    # consider angle etc
    # TODO
    return BOT_KICK


def pick_best_movement_commands(fieldstate: FieldState, desired_pos: Point, N: int = 3, dt_sec: float = 2):
    '''consider N combinations of movements and rotations. Pick the one that has the end position closed to desired position'''

    # do more interesting considerations like curves etc later. Right now, turn to target and drive toward it.
    delta_x = desired_pos.x - fieldstate.our_bot_pos_in.x
    delta_y = desired_pos.y - fieldstate.our_bot_pos_in.y

    try:
        angle_from_3oclock_to_pos = math.atan(delta_y/delta_x)
    except ZeroDivisionError:
        angle_from_3oclock_to_pos = np.pi/2

    angle_wrt_bot = angle_from_3oclock_to_pos - fieldstate.our_bot_bearing_rad

    print("degrees from horizontal", round(math.degrees(angle_from_3oclock_to_pos)))
    print("degrees wrt bot bearing", round(math.degrees(angle_wrt_bot)))

    pass


def consider_command(fieldstate: FieldState, command_str: str, duration_sec: float = 2) -> Point:
    '''given a command and duration, return the expected end position'''

    # default to nothing happening
    pos_end : Point = fieldstate.our_bot_pos_in
    bot_pos_start : Point = fieldstate.our_bot_pos_in
    bot_bearing : float = fieldstate.our_bot_bearing_rad

    if command_str == BOT_FORWARD:
        displacement = in_per_sec_forward * duration_sec
        pos_end.x = bot_pos_start.x + displacement * math.cos(bot_bearing)
        pos_end.y = bot_pos_start.y + displacement * math.sin(bot_bearing)

    # TODO FIXME
    # add considerations for the other commands


    return pos_end
        




def get_closest_point_to_desired_pos(point_list: list[Point], desired_pos: Point) -> Point:
    '''iterate through the points and find the shortest hypot'''

    best_dis : float = np.inf
    best_point : Point = point_list[0]
    for point in point_list:
        delta_x = abs(point.x - desired_pos.x)
        delta_y = abs(point.y - desired_pos.y)
        dis_to_desired_pos = math.sqrt(pow(delta_x,2) + pow(delta_y,2))

        if dis_to_desired_pos <= best_dis:
            best_dis = dis_to_desired_pos
            best_point = point


    return best_point


if __name__ == "__main__":
    main()