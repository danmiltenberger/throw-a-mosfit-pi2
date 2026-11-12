from tam_decide import solve_bot_from_goalpost, GOALPOST_NORTHWEST, GOALPOST_NORTHEAST, FIELD_GOAL_CENTER_BOTTOM
from tam_classes import Point
from tam_frame import get_field_frame, show_frame
from tam_draw import draw_robot_to_field, draw_arrow_point_to_point
from tam_colors import FUCHSIA, GREEN

def test_solve_bot_from_goalpost():

    dis_to_left = 144
    dis_to_right = 144
    goalpost_left = GOALPOST_NORTHWEST
    prev_pos = FIELD_GOAL_CENTER_BOTTOM


    bot_pos = solve_bot_from_goalpost(
        left_post_pos_in= goalpost_left,
        facing_north= True,
        right_post_dis_in= dis_to_right,
        left_post_dis_in= dis_to_left,
        prev_pos= prev_pos
    )

    field_frame = get_field_frame(
        USE_DRAWN_FIELD=True, 
        left_is_green=True)

    field_frame = draw_robot_to_field(
        field_frame=field_frame,
        pos_in= bot_pos
    )

    field_frame = draw_arrow_point_to_point(
        color= GREEN,
        start= bot_pos,
        end= GOALPOST_NORTHWEST,
        frame=field_frame,
        is_in_inches=True
    )

    field_frame = draw_arrow_point_to_point(
        color= FUCHSIA,
        start= bot_pos,
        end= GOALPOST_NORTHEAST,
        frame=field_frame,
        is_in_inches=True
    )

    show_frame(field_frame)



test_solve_bot_from_goalpost()