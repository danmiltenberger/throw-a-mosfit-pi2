import I2C_LCD_driver
from time import sleep
import socket
from typing import Optional

# Source: https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# hostname 10.201.23.91

mylcd = I2C_LCD_driver.lcd()

def get_ip_address() -> Optional[str]:
    """Return this device's primary local IPv4 address, or None."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def write_lcd_lines(lines: list[str]) -> None:
    """Write up to four lines, truncating each to 19 characters.

    Unused rows and leftover characters are erased.
    Pass an empty list to blank all four rows.
    """

    LCD_ROWS = 4
    LCD_COLUMNS = 20
    MAX_LINE_LENGTH = 19  # Strictly less than 20 characters

    if len(lines) > LCD_ROWS:
        raise ValueError("write_lcd_lines accepts at most 4 lines.")

    for row in range(1, LCD_ROWS + 1):
        text = lines[row - 1] if row <= len(lines) else ""

        text = text.replace("\r", " ").replace("\n", " ")
        text = text[:MAX_LINE_LENGTH]

        mylcd.lcd_display_string(text.ljust(LCD_COLUMNS), row)


list_lines = ["hello", "line2", "line3", "line4"]
write_lcd_lines(list_lines)