from classes import FieldState, Point, BotCommand, get_capture_zone_point
from tam_library_analyze_field import is_within_rect, is_within_circ
from tam_library_draw_field import draw_field_from_field_state, get_field_frame
from tam_library import show_frame
from field_state_save_and_load import save_fieldstates_to_csv
from constants import *
from constants_points import *
from constants_rads import *
from variables_robot import *
from variables import *
import cv2
import time
import random


def main():

    # initial state
    print("creating initial state")
    fieldstate = FieldState(
        our_bot_pos_in= Point(10,10),
        our_bot_bearing_rad= BEARING_NORTH,
        ball_pos_in= Point(50,50),
        ball_vel_x_in_per_s= 3,
        ball_vel_y_in_per_s= 2,
    )

    # initial bot command placeholder (aka do nothing for 0 seconds)
    bot_command = BotCommand()

    original_field = get_field_frame()

    # start the timing logic
    previous_time = time.perf_counter()
    action_start_time = previous_time
    time_at_start = previous_time

    old_print_str = ""
    status = "begin"


    save_to_csv : bool = False


    while True:

        current_time = time.perf_counter()
        action_elapsed_time = current_time - action_start_time
        total_elapsed_time = current_time - time_at_start
        dt = current_time - previous_time
        previous_time = current_time


        field_frame = original_field.copy()


        # if the elapsed time is greater than the command time, get a new command
        if action_elapsed_time >= bot_command.dur_sec:
            previous_time = current_time
            action_start_time = current_time

            bot_command, status = get_bot_command(fieldstate)


        # update the position with the current command 
        fieldstate = update_our_bot_position(fieldstate, bot_command, dt)

        # update the position of the ball (like having it pretend to bounce off the wall)
        fieldstate = update_ball_position(fieldstate)

        # show the user what is happening
        field_frame = draw_field_from_field_state(field_frame= field_frame, state= fieldstate)
        
        # print information to terminal
        time_elapsed_str = f"{round(total_elapsed_time,1)}\t"
        command_str = f"{status}\t"
        dur_total_str = f"t: {round(action_elapsed_time,1)}/{round(bot_command.dur_sec,1)}\t"

        print_str = time_elapsed_str + command_str + dur_total_str

        # if print_str != old_print_str:
        #     old_print_str = print_str
        #     print(print_str)

        # optionally save to csv
        if save_to_csv:
            save_fieldstates_to_csv(fieldstates= [fieldstate], filepath="field_states/bot_decisions.csv")
        

        # show to user and handle quitting
        cv2.imshow(mat=field_frame, winname="bot_decisions")
        
        key = cv2.waitKey(10) & 0xFF

        if key in (27, ord("q")):
            break

        if cv2.getWindowProperty("bot_decisions", cv2.WND_PROP_VISIBLE) < 1:
            break


def update_our_bot_position(fieldstate: FieldState, command: BotCommand, dt: float) -> FieldState:
    # update the bot with the given command

    bot_command = command.com_str
    our_bot_bearing = fieldstate.our_bot_bearing_rad
    our_bot_field_pos = fieldstate.our_bot_pos_in

    # assume zero, to overwrite below
    vel_x = 0
    vel_y = 0

    if bot_command == BOT_FORWARD:
        # adjust the x and y from the bearing to the field

        vel_x = in_per_sec_forward * math.cos(our_bot_bearing)
        vel_y = in_per_sec_forward * math.sin(our_bot_bearing)

    elif bot_command == BOT_BACKWARD:
        vel_x = in_per_sec_backward * math.cos(our_bot_bearing) * -1
        vel_y = in_per_sec_backward * math.sin(our_bot_bearing) * -1


    elif bot_command == BOT_STRAFE_LEFT:
        strafe_offset_rad = np.pi / 2
        vel_x = in_per_sec_strafe * math.cos(our_bot_bearing + strafe_offset_rad)
        vel_y = in_per_sec_strafe * math.sin(our_bot_bearing + strafe_offset_rad)

    elif bot_command == BOT_STRAFE_RIGHT:
        strafe_offset_rad = -np.pi / 2
        vel_x = in_per_sec_strafe * math.cos(our_bot_bearing + strafe_offset_rad)
        vel_y = in_per_sec_strafe * math.sin(our_bot_bearing + strafe_offset_rad)

    elif bot_command == BOT_ROTATE_LEFT: 
        fieldstate.our_bot_bearing_rad += rad_per_sec_rotation * dt

    elif bot_command == BOT_ROTATE_RIGHT:
        fieldstate.our_bot_bearing_rad += rad_per_sec_rotation * dt * -1


    else:
        print(f"unexpected bot command, recieved {bot_command}. Set vel x and y to zero")

    our_bot_field_pos.x += vel_x * dt
    our_bot_field_pos.y += vel_y * dt


    return fieldstate


def update_ball_position(field_state: FieldState)-> FieldState:
    # update the ball position by considering the speed and position
    # also consider if the ball is theirs (and moves with their bot) or ours (and moves with ours)


    # TODO
    return field_state


def get_bot_command_straight_line(fieldstate: FieldState, end_pos: Point, deg_tol: float = 2, dur_max_sec : float = 3, print_verbose: bool = False) -> BotCommand:
    '''
    return a command to rotate to point at the end position OR 
    return a command to drive to that point'''

    bot_command = BotCommand()

    delta_y = fieldstate.our_bot_pos_in.y - end_pos.y
    delta_x = fieldstate.our_bot_pos_in.y - end_pos.y
    rad_tolerance = math.radians(deg_tol)
    command_duration : float = 0

    # determine angle to end position
    try:
        angle_from_3oclock_to_pos = math.atan(delta_y/delta_x)
    except ZeroDivisionError:
        angle_from_3oclock_to_pos = np.pi/2

    angle_wrt_bot = angle_from_3oclock_to_pos - fieldstate.our_bot_bearing_rad

    # if within an acceptable angle tolerance, drive to target
    if -rad_tolerance <= angle_wrt_bot <= rad_tolerance:
        bot_command.com_str = BOT_FORWARD

        #x = vel*t, so t = x/vel
        dis_to_target = math.hypot(delta_x, delta_y)
        command_duration = dis_to_target / in_per_sec_forward 

    # otherwise rotate to the target
    else:

        # if too far right,
        if angle_wrt_bot > rad_tolerance:
            bot_command.com_str = BOT_ROTATE_LEFT

        # if too far left
        elif angle_wrt_bot < -rad_tolerance:
            bot_command.com_str = BOT_ROTATE_RIGHT

        # theta = theta_dot * t, so t = theta/ theta_dot
        command_duration = abs(angle_wrt_bot / rad_per_sec_rotation)


    # double check that it won't take too long to execute the command
    if command_duration > dur_max_sec:
        bot_command.dur_sec = dur_max_sec
    else:
        bot_command.dur_sec = command_duration

    if print_verbose:
        obj_bearing = f"obj deg: {round(math.degrees(angle_from_3oclock_to_pos))}"
        bot_bearing = f"bot deg: {round(math.degrees(fieldstate.our_bot_bearing_rad))}"
        delta_bearing = f"angle_wrt deg: {round(math.degrees(angle_wrt_bot))}"
        bot_pos = f"bot pos: {fieldstate.our_bot_pos_in}"
        obj_pos = f"obj pos: {end_pos}"
        com = f"{bot_command.com_str} {round(bot_command.dur_sec,1)}"

        print(obj_bearing, bot_bearing, delta_bearing, bot_pos, obj_pos, com, sep="\t")




    return bot_command


def get_bot_command(fieldstate: FieldState) -> tuple[BotCommand, str]:

    # placeholder to then modify
    this_command = BotCommand()

    status = "UNDECIDED"

    # determine who has the ball so we can make decisions
    fieldstate = determine_ball_ownership(fieldstate)


    # if we have the ball
    if fieldstate.ball_is_ours:


        # draw the ball in our capture zone
        fieldstate = get_capture_zone_point(fieldstate)
        fieldstate.ball_pos_in = fieldstate.capture_zone_center

        # if we are close to the goal, kick
        if is_close_enough_to_goal(fieldstate.our_bot_pos_in):
            this_command.com_str = BOT_KICK
            status = "kicking ball"

        # otherwise move to their goal
        else:
            this_command = get_bot_command_straight_line(
                fieldstate=fieldstate, 
                end_pos= FIELD_GOALBOX_CENTER_TOP)
            status = "moving ball closer to their goal"

    # if they have the ball
    if fieldstate.ball_is_theirs:

        # move to our goal to block
        this_command = get_bot_command_straight_line(fieldstate=fieldstate, end_pos= FIELD_GOALBOX_CENTER_BOTTOM)
        status = "moving to our goal to defend"
    

    # if neither have the ball
    if (fieldstate.ball_is_ours == False) and (fieldstate.ball_is_theirs == False):

        # if we see the ball, move to it
        if fieldstate.ball_is_seen:
            this_command = get_bot_command_straight_line(fieldstate=fieldstate, end_pos= fieldstate.ball_pos_in)
            status = "moving to ball"


        # if we don't, look for it
        else:
            status = "looking for ball"


    print(status, this_command.com_str, round(this_command.dur_sec,2))

    return this_command, status



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