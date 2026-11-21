from tam_frame import load_video_as_list_of_frames, show_frame_in_loop, save_frame_as_png, concat_frames, resize_frame


vid_left = load_video_as_list_of_frames("training_data/1280_720_2026_11_13_16_17_LEFT.mp4")
vid_right = load_video_as_list_of_frames("training_data/1280_720_2026_11_13_16_17_RIGHT.mp4")

min_num_frames = min(len(vid_left), len(vid_right))

int_to_save : int = 0
save_on_pause : bool = True

for int_frame in range(min_num_frames):

    frame_left = vid_left[int_frame]
    frame_right = vid_right[int_frame]

    combined = concat_frames(frame_left, frame_right, "DOWN")
    resized = resize_frame(combined, 0.6)

    if show_frame_in_loop(resized):
        int_to_save = int_frame
        break

if save_on_pause:
    save_frame_as_png(vid_left[int_to_save])
    save_frame_as_png(vid_right[int_to_save])
