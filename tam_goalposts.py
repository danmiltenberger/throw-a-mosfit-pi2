import numpy as np
from tam_classes import Point
from tam_points import GOALPOST_NORTHEAST, GOALPOST_NORTHWEST, GOALPOST_SOUTHEAST, GOALPOST_SOUTHWEST
from tam_constants import HAT_FUCHSIA, HAT_GREEN, HSV_HI, HSV_LO



def trig_from_goalposts(
        left_frame: np.ndarray, 
        right_frame: np.ndarray, 
        search_dict: dict,
        prev_bot_pos: Point,
        prev_bot_rad : float,
        left_is_green: bool = False,
        facing_north: bool = False,
        
        ) -> tuple[Point, float]:
    '''from two frames that might contain goalpost corner markers (green or purple), determine the bot's position and bearing. 
    If unable, returns given bot posiiton and bearing.'''

    purple_lo = search_dict[HAT_FUCHSIA][HSV_LO]
    purple_hi = search_dict[HAT_FUCHSIA][HSV_HI]

    green_lo = search_dict[HAT_GREEN][HSV_LO]
    green_hi = search_dict[HAT_GREEN][HSV_HI]

    goalpost_horizontal_dis_in = 48
    goalpost_vertical_dis_in = 23







