from I2C_write import write_lcd_lines, get_ip_address
from tam_library import get_time_str


def startup():
    """Initialize the LCD and display the startup message."""
    # Initialize your LCD here using your existing LCD library.

    ip_address = get_ip_address()

    write_lines = [
        "Throw a Mosfit! Time:" + get_time_str(),
        f"ip: {ip_address}",
        f"lets get to work!",
    ]

    write_lcd_lines(write_lines)

    print("LCD startup function ran.", flush=True)


if __name__ == "__main__":
    startup()