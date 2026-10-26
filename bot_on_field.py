from tam_library_draw_field import draw_field_from_field_state, get_field_frame
from tam_library_analyze_field import is_on_line, is_within_circ, is_within_rect
from tam_library import show_frame
from field_state_save_and_load import save_fieldstates_to_csv
from classes import FieldState, Point, Line, get_capture_zone_point
from constants import *
from constants_rads import *
from constants_points import *
from variables import *
from variables_robot import *
import time
import cv2
import math


def update_ball_position(fieldstate: FieldState, dt: float) -> FieldState:

    # check if the edge of the ball would collide with the wall
    # first lets just see if it's within a rectangle
    # that is away from the walls. If so, quick update

    # NOT DONE TODO FIXME

    ball_pos_in = fieldstate.ball_pos_in

    dis_from_sides_in = 12

    quick_rect_top_left = Point(
        x=FIELD_NORTHWEST_CORNER.x + dis_from_sides_in,
        y=FIELD_NORTHWEST_CORNER.y - dis_from_sides_in,
    )

    quick_rect_bot_right = Point(
        x=FIELD_SOUTHEAST_CORNER.x - dis_from_sides_in,
        y=FIELD_SOUTHEAST_CORNER.y + dis_from_sides_in,
    )

    if is_within_rect(
        point_in_q=ball_pos_in,
        top_left=quick_rect_top_left,
        bot_right=quick_rect_bot_right,
    ):

        # update ball position
        fieldstate.ball_pos_in.x += fieldstate.ball_vel_x_in_per_s * dt
        fieldstate.ball_pos_in.y += fieldstate.ball_vel_y_in_per_s * dt
        # print("is within center field rect")
        return fieldstate

    # otherwise, let's check the walls
    edge_left = ball_pos_in.x - BALL_RED_RADIUS_IN
    edge_right = ball_pos_in.x + BALL_RED_RADIUS_IN

    edge_top = ball_pos_in.y + BALL_RED_RADIUS_IN
    edge_bottom = ball_pos_in.y - BALL_RED_RADIUS_IN

    # check left
    if edge_left < FIELD_SOUTHWEST_CORNER.x:
        fieldstate.ball_vel_x_in_per_s *= -1
        print("bounce off left wall")

    # check right
    elif edge_right > FIELD_SOUTHEAST_CORNER.x:
        fieldstate.ball_vel_x_in_per_s *= -1
        print("bounce off right wall")

    # now examine if it might have gone in the goals
    elif is_on_line(ball_pos_in, line_goal_top):
        print("GOAL TOP")
        fieldstate.ball_vel_x_in_per_s = 0
        fieldstate.ball_vel_y_in_per_s = 0

    elif is_on_line(ball_pos_in, line_goal_bot):
        print("GOAL BOTTOM")
        fieldstate.ball_vel_x_in_per_s = 0
        fieldstate.ball_vel_y_in_per_s = 0

    # check top walls
    elif edge_top > FIELD_NORTHEAST_CORNER.y:
        fieldstate.ball_vel_y_in_per_s *= -1
        print("bounce off top wall")

    # check bottom walls
    elif edge_bottom < FIELD_SOUTHEAST_CORNER.y:
        fieldstate.ball_vel_y_in_per_s *= -1
        print("bounce off bottom wall")

    # update ball position
    fieldstate.ball_pos_in.x += fieldstate.ball_vel_x_in_per_s * dt
    fieldstate.ball_pos_in.y += fieldstate.ball_vel_y_in_per_s * dt

    print(fieldstate.ball_pos_in)

    return fieldstate


def update_bot_position(
    fieldstate: FieldState, bot_command: str, dt: float
) -> FieldState:
    # from a given command (like forward, strafe left, ...) move the robot

    our_bot_field_pos = fieldstate.our_bot_pos_in
    our_bot_bearing = fieldstate.our_bot_bearing_rad

    # assume no velocity, overwrite below
    vel_x: float = 0
    vel_y: float = 0

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


def update_who_has_ball(fieldstate : FieldState) -> FieldState:
    '''consider if the ball is within a 'capture zone' for our bot, their bot, or neither'''

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


def simulate_bot(field_state: FieldState, command_list: list, save_to_csv: bool = False, ):
    # have the bot move around given a list
    # of instructions

    field = get_field_frame()
    window_name = "bot_on_field"

    previous_time = time.perf_counter()
    action_start_time = previous_time
    time_at_start = previous_time

    command_step: int = 0
    while True:

        current_time = time.perf_counter()

        action_elapsed_time = current_time - action_start_time
        total_elapsed_time = current_time - time_at_start

        dt = current_time - previous_time
        previous_time = current_time

        bot_command = command_list[command_step]

        field_state = update_bot_position(
            fieldstate=field_state, dt=dt, bot_command=bot_command[BOT_ACTION]
        )

        field_state = update_who_has_ball(field_state)

        print(
            f"{round(total_elapsed_time,1)}", 
            f"{bot_command[BOT_ACTION]}",
            f" {round(action_elapsed_time,1)}/{round(bot_command[BOT_ACTION_DURATION_SEC])}",
            f"bearing: {round(math.degrees(field_state.our_bot_bearing_rad))}",
            f"ball_is_ours: {field_state.ball_is_ours}"
        )

        if action_elapsed_time > bot_command[BOT_ACTION_DURATION_SEC]:
            previous_time = current_time
            action_start_time = current_time
            command_step += 1

            if (command_step + 1) > (len(command_list)):
                print("commands complete")
                break

        copy_field = field.copy()

        copy_field = draw_field_from_field_state(
            field_frame=copy_field, state=field_state
        )

        if save_to_csv:
            save_fieldstates_to_csv(fieldstates= [field_state], filepath="field_states/bot_on_field.csv")

        cv2.imshow(mat=copy_field, winname=window_name)

        key = cv2.waitKey(10) & 0xFF

        if key in (27, ord("q")):
            break

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break


def simulate_ball():

    field_state = FieldState(
        our_bot_pos_in=Point(48, 12),
        ball_pos_in=Point(48, 48),
        ball_vel_x_in_per_s=10,
        ball_vel_y_in_per_s=10,
    )

    field = get_field_frame()

    window_name = "bot_on_field"

    previous_time = time.perf_counter()

    while True:

        current_time = time.perf_counter()
        dt = current_time - previous_time
        previous_time = current_time

        field_state = update_ball_position(fieldstate=field_state, dt=dt)

        copy_field = field.copy()

        copy_field = draw_field_from_field_state(
            field_frame=copy_field, state=field_state
        )

        cv2.imshow(mat=copy_field, winname=window_name)

        key = cv2.waitKey(10) & 0xFF

        if key in (27, ord("q")):
            break

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()


def test_is_within_rect():

    point_q = Point(0, 0)

    top_left = Point(0, 10)
    bot_right = Point(10, 0)

    rect_verdict = is_within_rect(
        point_in_q=point_q, top_left=top_left, bot_right=bot_right
    )

    print(rect_verdict)


if __name__ == "__main__":

    forward_3 = {BOT_ACTION: BOT_FORWARD, BOT_ACTION_DURATION_SEC: 3,}
    backward_3 = {BOT_ACTION: BOT_BACKWARD, BOT_ACTION_DURATION_SEC: 3,}
    strafe_left2 = {BOT_ACTION: BOT_STRAFE_LEFT, BOT_ACTION_DURATION_SEC: 2}
    strafe_right2 = {BOT_ACTION: BOT_STRAFE_RIGHT, BOT_ACTION_DURATION_SEC: 2}
    rot_left_4 = {BOT_ACTION: BOT_ROTATE_LEFT, BOT_ACTION_DURATION_SEC: 4 }
    rot_right_4 = {BOT_ACTION: BOT_ROTATE_RIGHT, BOT_ACTION_DURATION_SEC: 4 }

    command_list = [forward_3, forward_3, rot_left_4, strafe_right2]

    init_field = FieldState(
        ball_pos_in= FIELD_CENTER,
        our_bot_pos_in= FIELD_GOALBOX_CENTER_BOTTOM,
    )
    simulate_bot(
        save_to_csv= False, 
        command_list= command_list, 
        field_state= init_field)

    # test_is_on_line()
    # test_is_within_rect()
