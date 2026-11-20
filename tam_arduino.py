import time
from tam_commands import (
    BotCommand,
    BOT_FORWARD, BOT_BACKWARD, BOT_ROTATE_LEFT, BOT_ROTATE_RIGHT,
    BOT_STRAFE_LEFT, BOT_STRAFE_RIGHT, ARDUINO_MAX_DURATION
)
import serial

# Commands the current Arduino sketch understands
SUPPORTED_MOVES = {
    BOT_FORWARD, BOT_BACKWARD, BOT_ROTATE_LEFT,
    BOT_ROTATE_RIGHT, BOT_STRAFE_LEFT, BOT_STRAFE_RIGHT,
}

def connect(port, baud=9600, timeout=60):
    """Open the serial port and wait for the Arduino to finish its startup test."""
    ser = serial.Serial(port, baud, timeout=1)
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(f"[arduino] {line}")
        if line.startswith("Ready"):
            return ser
    ser.close()
    raise TimeoutError("Arduino did not report Ready in time")


def format_bot_command(cmd: BotCommand) -> str:
    """Turn a BotCommand into the wire format, e.g. 'Q_0.500_50'."""
    letter = cmd.com_str.upper()
    if letter not in SUPPORTED_MOVES:
        raise ValueError(
            f"Command '{cmd.com_str}' isn't supported by the Arduino sketch yet"
        )
    if cmd.dur_sec <= 0:
        raise ValueError("Duration must be positive")

    duration = min(cmd.dur_sec, ARDUINO_MAX_DURATION)
    percent = max(1, min(100, round(cmd.speed_percent)))  # sketch expects an int 1-100
    return f"{letter}_{duration:.3f}_{percent}"


def send_bot_command(ser, cmd: BotCommand, wait=True):
    """Format a BotCommand and send it. Blocks until 'Done' unless wait=False."""
    line = format_bot_command(cmd)
    ser.write(f"{line}\n".encode())
    ser.flush()

    if not wait:
        return

    deadline = time.time() + min(cmd.dur_sec, ARDUINO_MAX_DURATION) + 5
    while time.time() < deadline:
        reply = ser.readline().decode(errors="ignore").strip()
        if not reply:
            continue
        print(f"[arduino] {reply}")
        if reply.startswith("Error"):
            raise RuntimeError(reply)
        if reply == "Done":
            return
    raise TimeoutError("No 'Done' response from Arduino")