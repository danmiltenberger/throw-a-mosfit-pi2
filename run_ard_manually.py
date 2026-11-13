import re
import time
import serial #type: ignore

PORT = "/dev/ttyACM0"   # Linux Mega is usually /dev/ttyACM0 (or /dev/ttyUSB0)
BAUD = 115200           # must match Serial.begin() in the sketch
MAX_DURATION_S = 10.0   # matches MAX_DURATION_S in the Arduino code

COMMAND_PATTERN = re.compile(r"^([WASDQE])(\d+(\.\d+)?)$")

HELP_TEXT = """
Commands: <letter><seconds>, e.g. W2.0
  W = forward     S = backward
  A = strafe left D = strafe right
  Q = rotate left E = rotate right
Type 'quit' to exit.
"""


def read_arduino_output(ser, quiet_time=0.5):
    """Print everything the Arduino sends until it goes quiet."""
    last_data = time.time()
    while time.time() - last_data < quiet_time:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8", errors="replace").rstrip()
            if line:
                print(f"  Arduino: {line}")
            last_data = time.time()
        else:
            time.sleep(0.01)


def prompt_and_send(ser):
    """Prompt for one command, validate it, and send it to the Arduino.

    Returns False if the user asked to quit, otherwise True.
    """
    user_input = input("Command (e.g. W2.0, 'help', 'quit'): ").strip().upper()

    if user_input in ("QUIT", "EXIT"):
        return False
    if user_input == "HELP":
        print(HELP_TEXT)
        return True

    match = COMMAND_PATTERN.match(user_input)
    if not match:
        print("Invalid command. Use a letter (W/A/S/D/Q/E) followed by seconds, e.g. W2.0")
        return True

    duration = float(match.group(2))
    if duration <= 0:
        print("Duration must be greater than 0.")
        return True
    if duration > MAX_DURATION_S:
        print(f"Duration capped at {MAX_DURATION_S} s by the Arduino.")

    ser.write((user_input + "\n").encode("utf-8"))   # newline ends the command
    print(f"Sent: {user_input}")
    read_arduino_output(ser)
    return True


def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
    except serial.SerialException as e:
        print(f"Could not open {PORT}: {e}")
        return

    with ser:
        time.sleep(2)            # the Mega resets when the port opens; wait for it to boot
        ser.reset_input_buffer()
        read_arduino_output(ser) # show the startup message
        print(HELP_TEXT)

        try:
            while prompt_and_send(ser):
                pass
        except KeyboardInterrupt:
            print("\nExiting.")


if __name__ == "__main__":
    main()