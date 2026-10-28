import numpy as np
import math
from constants import *

# Programming settings
DEBUG_PRINT: bool = True
USE_DRAWN_FIELD : bool = True


# Performance settings
RUN_SYSTEM_CHECK: bool = True

### Search For
# balls (red in game, tennis ball for training)
search_for_ball_red: bool = True
search_for_ball_yellow: bool = True

# team colors (speed up searching by not looking for ourselves, for example)
search_for_hat_blue: bool = True
search_for_hat_yellow: bool = True

# goalposts
search_for_hat_fuchsia: bool = False
search_for_hat_green: bool = False


def get_search_for_list() -> list:
    search_list= []

    if search_for_ball_red:
        search_list.append(BALL_RED)

    if search_for_ball_yellow:
        search_list.append(BALL_YELLOW)

    if search_for_hat_blue:
        search_list.append(HAT_BLUE)

    if search_for_hat_yellow:
        search_list.append(HAT_YELLOW)

    if search_for_hat_fuchsia:
        search_list.append(HAT_FUCHSIA)

    if search_for_hat_green:
        search_list.append(HAT_GREEN)

    return search_list


### Draw to Field
draw_ball_red : bool = True
draw_ball_yellow : bool = True
draw_our_bot : bool = True
draw_our_bot_capture_zone : bool = False
draw_their_bot : bool = False
draw_target_pos : bool = True

draw_arrow_to_target : bool = False

### Write to field
write_ball_red : bool = False
write_our_bot : bool = True