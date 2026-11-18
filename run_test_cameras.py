from tam_binocular import setup_left_right_cams, get_left_right_frames
from tam_frame import show_frame_in_loop, concat_frames, resize_frame
from tam_draw import add_text_top


camL, camR = setup_left_right_cams()

while True:
    resize_float = input("resize frame? hit enter for 1 otherwise enter a value: ")
    if resize_float == "":
        resize_float = 1
        break

    try:
        resize_float = float(resize_float)
    except:
        print(f"unable to convert {resize_float} to float. Need value between 0 and 1")


while True:

    frameL, frameR = get_left_right_frames(cam_left=camL, cam_right= camR)

    frameL = add_text_top(frameL,"LEFT")
    frameR = add_text_top(frameR,"RIGHT")

    frame_both = concat_frames(frameL, frameR, "DOWN")
    frame_both = resize_frame(frame_both, resize_float)

    if show_frame_in_loop(frame_both) == False:
        break




