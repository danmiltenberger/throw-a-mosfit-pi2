from tam_arduino import send_command_to_arduino
from tam_classes import BotCommand
from tam_switches import get_switches_status_dict, setup_switches, print_switch_status
from tam_commands import *
from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_frame import show_frame_in_loop, concat_frames



def system_check():
    '''Go through all our systems and make sure things are working'''


    # setup and test switches
    print("setting up switches")
    setup_switches()
    while True:
        try:
            print_switch_status()
        except KeyboardInterrupt:
            break

    # setup and test cameras
    print("setting up cameras")
    left_cam, right_cam = setup_left_right_cams()

    while True:
        left_frame, right_frame = get_left_right_frames(left_cam, right_cam)
        combined = concat_frames(left_frame, right_frame, "DOWN")

        if show_frame_in_loop(combined):
            break

    # test forward
    forward2 = BotCommand(BOT_FORWARD, 2)

    # test backward
    backward2 = BotCommand(BOT_BACKWARD,2)

    # test left
    strafeleft2 = BotCommand(BOT_STRAFE_LEFT,2)

    # test right
    straferight2 = BotCommand(BOT_STRAFE_RIGHT,2)

    # test gate
    bot_kick = BotCommand(BOT_KICK,1)

    # TODO!

    pass

if __name__ == "__main__":
    system_check()