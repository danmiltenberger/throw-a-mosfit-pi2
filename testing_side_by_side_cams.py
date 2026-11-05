#!/usr/bin/env python3
import os
from datetime import datetime

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from pynput import keyboard

# ----- Settings -----
OUTPUT_DIR = "recordings"
WIDTH, HEIGHT = 1280, 720
FPS = 30
BITRATE = 10_000_000  # 10 Mbps

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Camera 0 = LEFT, camera 1 = RIGHT
# Swap these if your physical cameras are reversed.
cameras = {
    "LEFT": Picamera2(0),
    "RIGHT": Picamera2(1),
}

for side, cam in cameras.items():
    config = cam.create_video_configuration(
        main={"size": (WIDTH, HEIGHT), "format": "RGB888"},
        controls={"FrameRate": FPS},
    )
    cam.configure(config)
    cam.start()

print("Cameras running.")
print("Press SPACE to start/stop recording. Press ESC to quit.")

recording = False
encoders = {}


def timestamp_for_filename():
    # Matches: 2026_11_4_T_18_09
    now = datetime.now()
    return f"{now.year}_{now.month}_{now.day}_T_{now.hour}_{now.minute:02d}"


def start_recording():
    global recording, encoders

    ts = timestamp_for_filename()

    for side, cam in cameras.items():
        filename = os.path.join(
            OUTPUT_DIR,
            f"{WIDTH}_{HEIGHT}_{side}_{ts}.mp4"
        )
        encoder = H264Encoder(bitrate=BITRATE)
        output = FfmpegOutput(filename)

        cam.start_recording(encoder, output)
        encoders[side] = (cam, encoder, filename)
        print(f"Recording {side}: {filename}")

    recording = True


def stop_recording():
    global recording, encoders

    for side, (cam, encoder, filename) in encoders.items():
        cam.stop_recording()
        print(f"Saved {side}: {filename}")

    encoders = {}
    recording = False


def on_press(key):
    global recording

    if key == keyboard.Key.space:
        if recording:
            stop_recording()
        else:
            start_recording()

    elif key == keyboard.Key.esc:
        if recording:
            stop_recording()
        return False  # Stop listener


try:
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
finally:
    for cam in cameras.values():
        cam.stop()
    print("Cameras stopped.")