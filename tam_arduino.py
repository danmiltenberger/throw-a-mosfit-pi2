from tam_classes import BotCommand
import time
import serial
from tam_lcd import write_lcd_lines


# to get the port run >python3 -m serial.tools.list_ports -v
ARDUINO_PORT = "/dev/ttyACM0"  # Replace with ard serial port
ARDUINO_BAUD = 115200          # must match PI_Serial in arduino_main.ino

_arduino = None

def _read_line_starting_with(connection, prefix: str, timeout_sec: float) -> str: # PHOEBE CHANGED I added this function
    """Read lines until one starts with prefix. The Arduino's debug prints ("dead ahead", etc.) are skipped."""
    deadline = time.perf_counter() + timeout_sec
    while time.perf_counter() < deadline:
        line = connection.readline().decode("utf-8", errors="ignore").strip()
        if line.startswith(prefix):
            return line
        if line:
            print(f"[arduino] {line}")
    raise TimeoutError(f"No '{prefix}' from the Arduino within {timeout_sec}s")


def get_arduino(): # PHOEBE CHANGED I added this function
    global _arduino
    if _arduino is None:
        _arduino = serial.Serial(port=ARDUINO_PORT, baudrate=ARDUINO_BAUD, timeout=1, write_timeout=1)
        _read_line_starting_with(_arduino, "READY", timeout_sec=5)   # wait for setup() to finish
        _arduino.reset_input_buffer()
    return _arduino


def close_arduino():
    """Close the port (call at the end of a match / program)."""
    global _arduino
    if _arduino is not None:
        _arduino.close()
        _arduino = None


def send_command_to_arduino(command: BotCommand) -> str: # PHOEBE CHANGED I added this function
    """Send one command, e.g. BotCommand("W", 0.15) -> "W150". Returns the Arduino's ACK line."""
    arduino = get_arduino()

    send_str = command.com_str + str(round(command.dur_sec * 1000)) #PHOEBE CHANGED round("already there" * 1000)
    print(f"linux sent: {send_str}")

    arduino.write((send_str + "\n").encode("utf-8"))

    # ACK <command> <left sensor> <right sensor>. Kick/arms block the Arduino ~2.3 s, so allow 3 s.
    response = _read_line_starting_with(arduino, "ACK", timeout_sec=3)
    print("Arduino replied:", response)

    write_lcd_lines([
        f"RPi sent: {send_str}",
        f"Ard rciv: {response}",
    ])

    return response


if __name__ == "__main__":
    #bot_command = BotCommand() # PHOEBE CHANGED grayed out
    #send_command_to_arduino(bot_command) # PHOEBE CHANGED I grayed out
    from tam_commands import BOT_FORWARD
    send_command_to_arduino(BotCommand(BOT_FORWARD, 0.2))
    send_command_to_arduino(BotCommand(BOT_FORWARD, 0.2))   # second one reuses the open port
    close_arduino()


# def send_to_arduino(connection, message): # PHOEBE CHANGED I grayed out
#     """Send one line and return the Arduino's response."""
#     connection.write((message + "\n").encode("utf-8"))
#     connection.flush()

#     reply = connection.readline()

#     if not reply.endswith(b"\n"):
#         pass
#         #raise TimeoutError("No complete reply received from the Arduino.")

#     return reply.decode("utf-8").rstrip("\r\n")


# def send_command_to_arduino(command : BotCommand): # PHOEBE CHANGED I garyed this out, orginal func
#     port = "/dev/ttyACM0"  # Replace with ard serial port

#     print(f"attempting communication with {port}")

#     send_str = command.com_str + str(round(command.dur_sec * 1000))  

#     print(f"linux sent: {send_str}")

#     with serial.Serial(
#         port=port,
#         baudrate=115200,
#         timeout=3,
#         write_timeout=3,
#     ) as arduino:
#         # Allow startup time before sending the first message.
#         time.sleep(2)
#         arduino.reset_input_buffer()

#         response = send_to_arduino(arduino, send_str)
#         print("Arduino replied:", response)

#     write_lcd_lines([
#         f"RPi sent: {send_str}",
#         f"Ard rciv: {response}",
#     ])

  
