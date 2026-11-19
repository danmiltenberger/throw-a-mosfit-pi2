import time
import serial  # pip install pyserial

VALID_DIRECTIONS = set("WASDQE")
ARDUINO_MAX_DURATION = 30.0  # matches MAX_DURATION_S in the sketch


def connect(port, baud=9600, timeout=60):
    """Open the serial port and wait for the Arduino to finish its startup test.

    Opening the port resets the Arduino, which then runs the ~20 s motor test
    before printing "Ready", so we wait for that line before returning.
    """
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
    """Send a movement command, e.g. send_command(ser, "W", 1.5).

    direction: W forward, S backward, A left, D right,
               Q rotate counterclockwise, E rotate clockwise
    duration:  seconds (float)
    wait:      if True, block until the Arduino reports "Done"
    """
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


if __name__ == "__main__":
    # Windows: "COM3"   Linux: "/dev/ttyACM0"   macOS: "/dev/cu.usbmodem*"
    ser = connect("/dev/ttyACM0")
    try:
        send_command(ser, "W", 1)      # forward 1 s
        send_command(ser, "Q", 1.2)    # rotate CCW 1.2 s
        send_command(ser, "D", 0.5)    # strafe right 0.5 s
    except KeyboardInterrupt:
        stop(ser)
    finally:
        ser.close()