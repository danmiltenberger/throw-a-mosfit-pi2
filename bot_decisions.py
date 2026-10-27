from classes import FieldState, Point, BotCommand
from tam_library_analyze_field import is_within_rect
from tam_library_draw_field import draw_field_from_field_state, get_field_frame
from tam_library import show_frame
from constants import *
from constants_points import *
from constants_rads import *
from variables_robot import *
from variables import *
import cv2
import time



def main():

    # initial state
    fieldstate = FieldState(
        our_bot_pos_in= FIELD_GOALBOX_CENTER_BOTTOM,
        our_bot_bearing_rad= BEARING_NORTH_EAST,
        ball_pos_in= FIELD_CENTER,
        ball_vel_x_in_per_s= 3,
        ball_vel_y_in_per_s= 2,
    )

    # initial bot command placeholder (do nothing for 0 seconds)
    bot_command = BotCommand()

    original_field = get_field_frame()

    # start the timing logic
    time_start = time.perf_counter()
    time_command_started = time_start

    waiting_for_command : bool = True

    

    while True:

        field_frame = original_field.copy()

        time_current = time.perf_counter()
        time_elapsed = time_current - time_start

        time_command_elasped = time_current - time_command_started

 
        # if the elapsed time is greater than the command time, get a new one
        if time_command_elasped >= bot_command.dur_sec:
            waiting_for_command = True
        else:
            waiting_for_command = False

        # get the next command after the command is completed
        if waiting_for_command:
            bot_command = get_bot_command(fieldstate)

        # update the position with the current command (example, 1.8 seconds through DRIVE_FORWARD_2sec)
        fieldstate = update_our_bot_position(fieldstate, bot_command)

        # update the position of the ball (like having it pretend to bounce off the wall)
        fieldstate = update_ball_position(fieldstate)

        # show the user what is happening
        field_frame = draw_field_from_field_state(field_frame= field_frame, state= fieldstate)

        cv2.imshow(mat=field_frame, winname="bot_decisions")
        
        key = cv2.waitKey(10) & 0xFF

        if key in (27, ord("q")):
            break

        if cv2.getWindowProperty("bot_decisions", cv2.WND_PROP_VISIBLE) < 1:
            break


def update_our_bot_position(fieldstate: FieldState, bot_command: BotCommand) -> FieldState:
    # update the bot with the given command

    # basically implement many of the processes in bot_on_field

    # TODO

    return fieldstate


def update_ball_position(field_state: FieldState)-> FieldState:
    # update the ball position by considering the speed and position
    # also consider if the ball is theirs (and moves with their bot) or ours (and moves with ours)


    # TODO
    return field_state



def get_bot_command(fieldstate: FieldState) -> BotCommand:

    # placeholder to then modify
    this_command = BotCommand()

    # determine who has the ball to then make decisions

    # if we have the ball

        # if we are far from the goal


        # if we are close to the goal


    # if they have the ball
        # move to the goal
    


    # if neither have the ball
        # if we see the ball, move to it


        # if we don't, look for it



    # TODO


    return this_command


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


def get_end_pos_from_command(fieldstate: FieldState, command_str: str, duration_sec: float = 2) -> Point:
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
        

def has_N_seconds_passed(time_start: float, N_sec: float) -> bool:
    '''has N seconds passed since the time start?'''
    current_time = time.perf_counter()

    if abs(time_start - current_time) >= N_sec:
        return True
    else:
        return False


def get_closest_point_to_desired_pos(point_list: list[Point], desired_pos: Point) -> Point:
    '''iterate through the points and find the shortest hypotenuse'''

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