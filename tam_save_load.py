import csv
from tam_constants import BALL_RED, HAT_BLUE, HAT_GREEN, HAT_YELLOW, HAT_FUCHSIA
from tam_classes import FieldState, Detection
from tam_decide import get_init_fieldstate
from datetime import datetime
from tam_colors import YELLOW
import os




# functions to save and load training outputs


def main():
    # testing functions
    fs = get_init_fieldstate()

    write_fs_and_detects_to_csv(fs=fs)


def get_iso_str(include_sec:bool = False):
    '''return a string format YYYY_MM_DD_HOUR_MIN and optionally +_SEc'''

    if include_sec:
        return datetime.now().strftime("%Y_%m_%d_T%H_%M_%S")
    else:
        return datetime.now().strftime("%Y_%m_%d_T%H_%M")

def print_dict(dict: dict):
    '''print key (tab) value'''

    for key in dict.keys():
        print(str(key), str(dict[key]), sep="\t")



list_headers = [
    "timestep_sec",

    # left camera
    "camL_ball_x_px",
    "camL_ball_y_px",
    "camL_ball_w_px",   # width in pixels

    "camL_gpgr_x_px",   # goalpost green
    "camL_gpgr_y_px",
    "camL_gpgr_w_px",
    
    "camL_gppr_x_px",   # goalpost purple
    "camL_gppr_y_px",
    "camL_gppr_w_px",

    "camL_tbot_x_px",   # their bot
    "camL_tbot_y_px",   
    "camL_tbot_w_px",

    # right camera
    "camR_ball_x_px",
    "camR_ball_y_px",
    "camR_ball_w_px",

    "camR_gpgr_x_px",   # goalpost green
    "camR_gpgr_y_px",
    "camR_gpgr_w_px",

    "camR_gppr_x_px",   # goalpost purple
    "camR_gppr_x_px",
    "camR_gppr_w_px",

    "camR_tbot_x_px",   # their bot
    "camR_tbot_y_px",   
    "camR_tbot_w_px",

    # field
    "fild_ball_x_in",
    "fild_ball_y_in",

    "fild_tbot_x_in",   # their bot
    "fild_tbot_y_in",   
    "fild_tbot_brad",   # their bot bearing radians

    "fild_obot_x_in",   # our bot
    "fild_obot_y_in",   
    "fild_obot_brad",   # our bot bearing radians
]


def get_dict_from_cam(
        dict_detections : dict[str, Detection], 
        is_left_cam: bool = True,
        our_team_is_yellow: bool = True) -> dict[str, str | float]:
    '''go through the detect list and format with the above headers'''

    if is_left_cam:
        label = "L"
    else:
        label = "R"


    ball_x = f"cam{label}_ball_x_px"
    ball_y = f"cam{label}_ball_y_px"
    ball_w = f"cam{label}_ball_w_px"   # width in pixels

    gpgr_x = f"cam{label}_gpgr_x_px"   # goalpost green
    gpgr_y = f"cam{label}_gpgr_y_px"
    gpgr_w = f"cam{label}_gpgr_w_px"
    
    gppr_x = f"cam{label}_gppr_x_px"   # goalpost purple
    gppr_y = f"cam{label}_gppr_y_px"
    gppr_w = f"cam{label}_gppr_w_px"

    tbot_x = f"cam{label}_tbot_x_px"   # their bot
    tbot_y = f"cam{label}_tbot_y_px" 
    tbot_w = f"cam{label}_tbot_w_px"

    dict_format = {}

    # add the ball
    ball_detect : Detection = dict_detections[BALL_RED]
    if ball_detect.in_frame:
        dict_format[ball_x] = ball_detect.camera_pos_px.x
        dict_format[ball_y] = ball_detect.camera_pos_px.y
        dict_format[ball_w] = ball_detect.width_px
    else:
        dict_format[ball_x] = "NA"
        dict_format[ball_y] = "NA"
        dict_format[ball_w] = "NA"

    # add the green goalpost
    gpgr_detect : Detection = dict_detections[HAT_GREEN]
    if gpgr_detect.in_frame:
        dict_format[gpgr_x] = gpgr_detect.camera_pos_px.x
        dict_format[gpgr_y] = gpgr_detect.camera_pos_px.y
        dict_format[gpgr_w] = gpgr_detect.width_px
    else:
        dict_format[gpgr_x] = "NA"
        dict_format[gpgr_y] = "NA"
        dict_format[gpgr_w] = "NA"

    # add the purple goalpost
    gppr_detect : Detection = dict_detections[HAT_FUCHSIA]
    if gppr_detect.in_frame:
        dict_format[gppr_x] = gppr_detect.camera_pos_px.x
        dict_format[gppr_y] = gppr_detect.camera_pos_px.y
        dict_format[gppr_w] = gppr_detect.width_px
    else:
        dict_format[gppr_x] = "NA"
        dict_format[gppr_y] = "NA"
        dict_format[gppr_w] = "NA"      

    # add the opponent
    if our_team_is_yellow:
        tbot_detect : Detection = dict_detections[HAT_BLUE]
    else:
        tbot_detect : Detection = dict_detections[HAT_YELLOW]

    if tbot_detect.in_frame:
        dict_format[tbot_x] = tbot_detect.camera_pos_px.x
        dict_format[tbot_y] = tbot_detect.camera_pos_px.y
        dict_format[tbot_w] = tbot_detect.width_px
    else:
        dict_format[tbot_x] = "NA"
        dict_format[tbot_y] = "NA"
        dict_format[tbot_w] = "NA" 

    return dict_format


def get_dict_from_field(fs: FieldState) -> dict[str, float]:
    '''format a dict from the fieldstate'''

    dict_format = {}

    # keys:
    ball_x = "fild_ball_x_in",
    ball_y = "fild_ball_y_in",

    tbot_x = "fild_tbot_x_in",   # their bot
    tbot_y = "fild_tbot_y_in",   
    tbot_r = "fild_tbot_brad",   # their bot bearing radians

    obot_x = "fild_obot_x_in",   # our bot
    obot_y = "fild_obot_y_in",   
    obot_r = "fild_obot_brad",   # our bot bearing radians


    # add ball info
    dict_format[ball_x] = fs.ball_pos_in.x
    dict_format[ball_y] = fs.ball_pos_in.y

    # add their bot info
    dict_format[tbot_x] = fs.their_bot_pos_in.x
    dict_format[tbot_y] = fs.their_bot_pos_in.y
    dict_format[tbot_r] = fs.their_bot_bearing_rad

    # add our bot info
    dict_format[obot_x] = fs.our_bot_pos_in.x
    dict_format[obot_y] = fs.our_bot_pos_in.y
    dict_format[obot_r] = fs.our_bot_bearing_rad

    return dict_format



def write_fs_and_detects_to_csv(
        fs: FieldState, 
        dict_detect_left : dict[str, Detection] = {}, 
        dict_detect_right : dict[str,Detection] = {},
        csv_file_name : str = "NO_NAME"):

    if csv_file_name == "NO_NAME":
        csv_file_name = get_iso_str()


    output_dir  = "training_output"

    try:
        os.mkdir(output_dir)
    except FileExistsError:
        pass

    csv_file_path = output_dir + csv_file_name + ".csv"

    if fs.our_team_color == YELLOW:
        is_team_yellow = True
    else:
        is_team_yellow = False


    dict_cam_left = get_dict_from_cam(
        dict_detections= dict_detect_left, 
        our_team_is_yellow=is_team_yellow,
        is_left_cam=True)

    dict_cam_right = get_dict_from_cam(
        dict_detections= dict_detect_right, 
        our_team_is_yellow=is_team_yellow,
        is_left_cam=False)

    dict_field = get_dict_from_field(fs)

    dict_data = {**dict_cam_left, **dict_cam_right, **dict_field}

    print_dict(dict_data)

    

    # # Writing to CSV
    # with open(csv_file_path, mode='w', newline='') as file:
    #     writer = csv.DictWriter(file, fieldnames=fieldnames)
    #     writer.writeheader()  # Write header row
    #     writer.writerows(cars)  # Write data rows
        

if __name__ == "__main__":
    main()