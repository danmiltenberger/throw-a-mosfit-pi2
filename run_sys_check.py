from tam_arduino import send_command_to_arduino
from tam_classes import BotCommand
from tam_commands import *


def system_check():
    '''Go through all our systems and make sure things are working'''

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