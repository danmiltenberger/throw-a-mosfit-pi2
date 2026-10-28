import time
import serial
from I2C_write import write_lcd_lines

# to get the port run >python3 -m serial.tools.list_ports -v


def send_to_arduino(connection, message):
    """Send one line and return the Arduino's response."""
    connection.write((message + "\n").encode("utf-8"))
    connection.flush()

    reply = connection.readline()

    if not reply.endswith(b"\n"):
        raise TimeoutError("No complete reply received from the Arduino.")

    return reply.decode("utf-8").rstrip("\r\n")


def main():
    port = "/dev/ttyACM0"  # Replace with your Arduino's serial port.

    print(f"attempting communication with {port}")

    send_str = "hello arduino!"
    print(f"linux sent: {send_str}")

    with serial.Serial(
        port=port,
        baudrate=9600,
        timeout=3,
        write_timeout=3,
    ) as arduino:
        # Allow startup time before sending the first message.
        time.sleep(2)
        arduino.reset_input_buffer()

        response = send_to_arduino(arduino, send_str)
        print("Arduino replied:", response)

    write_lcd_lines([
        f"RPi sent: {send_str}",
        f"Ard rciv: {response}",
    ])
    

if __name__ == "__main__":
    main()