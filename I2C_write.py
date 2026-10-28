import I2C_LCD_driver
from time import sleep
import socket
from typing import Optional

# Source: https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# hostname 10.201.23.91

mylcd = I2C_LCD_driver.lcd()

mylcd.lcd_display_string("This is how you", 1)
sleep(1)

mylcd.lcd_clear()

mylcd.lcd_display_string("clear the screen", 1)
sleep(1)

mylcd.lcd_clear()

mylcd = I2C_LCD_driver.lcd()

def get_ip_address() -> Optional[str]:
    """Return this device's primary local IPv4 address, or None."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None
mylcd.lcd_display_string("IP Address:", 1) 

mylcd.lcd_display_string(get_ip_address(), 2)