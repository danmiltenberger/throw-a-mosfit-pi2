import numpy as np
import math

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


### Draw to Field
draw_ball_red : bool = True
draw_ball_yellow : bool = True
draw_our_bot : bool = True
draw_our_bot_capture_zone : bool = False
draw_their_bot : bool = False


