import re
import time
import serial  # pip install pyserial

VALID_DIRECTIONS = set("WASDQE")
ARDUINO_MAX_DURATION = 30.0  # matches MAX_DURATION_S in the sketch

# Accepts "W1", "w 1.5", "Q.5", etc.
COMMAND_RE = re.compile(r"^([WASDQE])\s*(\d*\.?\d+)$", re.IGNORECASE)

HELP_TEXT = (
    "Commands: <direction><seconds>, e.g. W1, S0.5, Q1.2\n"
    "  W forward   S backward   A left   D right\n"
    "  Q rotate CCW   E rotate CW\n"
    "  X stop   H help   quit to exit"
)


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


def send_command(ser, direction, duration, wait=True):
    """Send a movement command, e.g. send_command(ser, "W", 1.5)."""
    direction = direction.upper()
    if direction not in VALID_DIRECTIONS:
        raise ValueError(f"Invalid direction '{direction}'. Use one of: WASDQE")
    if duration <= 0:
        raise ValueError("Duration must be positive")

    ser.write(f"{direction}{duration:.3f}\n".encode())
    ser.flush()

    if not wait:
        return

    deadline = time.time() + min(duration, ARDUINO_MAX_DURATION) + 5
    while time.time() < deadline:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        print(f"[arduino] {line}")
        if line.startswith("Error"):
            raise RuntimeError(line)
        if line == "Done":
            return
    raise TimeoutError("No 'Done' response from Arduino")


def stop(ser):
    """Immediately stop all motors."""
    ser.write(b"X\n")
    ser.flush()


def get_command(prompt="> "):
    """Ask the user for a command and validate it.

    Returns:
        (direction, duration)  for a valid movement command
        ("X", None)            for stop
        ("QUIT", None)         to exit
        None                   if the input was invalid or was a help request
    """
    text = input(prompt).strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered in ("quit", "exit"):
        return ("QUIT", None)
    if lowered in ("h", "help", "?"):
        print(HELP_TEXT)
        return None
    if lowered == "x":
        return ("X", None)

    match = COMMAND_RE.match(text)
    if not match:
        print(f"Invalid command '{text}'. Type H for help.")
        return None

    direction = match.group(1).upper()
    duration = float(match.group(2))

    if duration <= 0:
        print("Duration must be greater than 0.")
        return None
    if duration > ARDUINO_MAX_DURATION:
        print(f"Duration exceeds {ARDUINO_MAX_DURATION:g} s; the Arduino will cap it.")
        duration = ARDUINO_MAX_DURATION

    return (direction, duration)


def interactive_loop(ser):
    """Prompt for commands and send each valid one until the user quits."""
    print(HELP_TEXT)
    while True:
        try:
            result = get_command()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if result is None:
            continue

        direction, duration = result
        if direction == "QUIT":
            break

        try:
            if direction == "X":
                stop(ser)
                print(f"[arduino] {ser.readline().decode(errors='ignore').strip()}")
            else:
                send_command(ser, direction, duration)
        except KeyboardInterrupt:
            stop(ser)  # Ctrl+C mid-move stops the robot
            print("\nInterrupted, stop sent.")
        except (ValueError, RuntimeError, TimeoutError) as e:
            print(f"Error: {e}")

    stop(ser)


if __name__ == "__main__":
    # Windows: "COM3"   Linux: "/dev/ttyACM0"   macOS: "/dev/cu.usbmodem*"
    ser = connect("/dev/ttyACM0")
    try:
        interactive_loop(ser)
    finally:
        ser.close()