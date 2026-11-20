import curses
from tam_arduino import send_bot_command, connect
from tam_commands import BotCommand, BOT_FORWARD, BOT_ROTATE_LEFT, BOT_ROTATE_RIGHT
# NOTE: these three names are guesses. Change them to whatever tam_commands defines.
from tam_commands import BOT_BACKWARD, BOT_STRAFE_LEFT, BOT_STRAFE_RIGHT

# key -> (command constant, label)
KEY_MAP = {
    ord("w"): (BOT_FORWARD,      "Forward"),
    ord("s"): (BOT_BACKWARD,     "Backward"),
    ord("a"): (BOT_STRAFE_LEFT,  "Left"),
    ord("d"): (BOT_STRAFE_RIGHT, "Right"),
    ord("q"): (BOT_ROTATE_LEFT,  "Rotate CCW"),
    ord("e"): (BOT_ROTATE_RIGHT, "Rotate CW"),
}

STEP_DURATION_SEC = 0.2   # each keypress drives this long; hold a key to keep going
SPEED_PERCENT = 30
SPEED_STEP = 5
SPEED_MIN, SPEED_MAX = 10, 100


def draw_screen(stdscr, speed, status):
    stdscr.erase()
    stdscr.addstr(0, 0, "Manual drive")
    stdscr.addstr(2, 0, "  W forward    S backward")
    stdscr.addstr(3, 0, "  A left       D right")
    stdscr.addstr(4, 0, "  Q rotate CCW E rotate CW")
    stdscr.addstr(5, 0, "  + / -  speed    X quit")
    stdscr.addstr(7, 0, f"Speed: {speed}%   Step: {STEP_DURATION_SEC} s")
    stdscr.addstr(8, 0, f"Last: {status}")
    stdscr.refresh()


def drive_loop(stdscr, ser):
    curses.curs_set(0)
    stdscr.nodelay(False)   # block until a key is pressed
    stdscr.keypad(True)

    speed = SPEED_PERCENT
    status = "-"
    draw_screen(stdscr, speed, status)

    while True:
        key = stdscr.getch()
        if key in (ord("X"), ord("x")):
            break

        if key in (ord("+"), ord("=")):
            speed = min(SPEED_MAX, speed + SPEED_STEP)
            status = f"speed -> {speed}%"
        elif key in (ord("-"), ord("_")):
            speed = max(SPEED_MIN, speed - SPEED_STEP)
            status = f"speed -> {speed}%"
        else:
            entry = KEY_MAP.get(ord(chr(key).lower())) if 0 <= key < 256 else None
            if entry is None:
                continue
            command, label = entry
            status = label
            draw_screen(stdscr, speed, f"{label} (sending...)")
            send_bot_command(ser, BotCommand(command, dur_sec=STEP_DURATION_SEC,
                                             speed_percent=speed))
            # Drop key-repeat events buffered while the robot was moving,
            # so the bot stops soon after you release the key.
            curses.flushinp()

        draw_screen(stdscr, speed, status)


def manual_drive():
    # Connect first: opening the port resets the Arduino and runs its startup test
    ser = connect("/dev/ttyACM0")
    try:
        curses.wrapper(drive_loop, ser)
    finally:
        ser.close()


if __name__ == "__main__":
    manual_drive()