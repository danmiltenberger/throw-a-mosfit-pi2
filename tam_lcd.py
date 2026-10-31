### library for all LCD functions including actual and simulated LCD


# -*- coding: utf-8 -*-
# Original code found at:
# https://gist.github.com/DenisFromHR/cc863375a6e19dce359d

"""
Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
Made available under GNU GENERAL PUBLIC LICENSE

# Modified Python I2C library for Raspberry Pi
# as found on http://www.recantha.co.uk/blog/?p=4849
# Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
# added bits and pieces from various sources
# By DenisFromHR (Denis Pleic)
# 2015-02-10, ver 0.1

"""

# i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
I2CBUS = 1

# LCD Address
ADDRESS = 0x27

import smbus
from time import sleep
from typing import Optional
import socket
import numpy as np
from tam_classes import FieldState

class i2c_device:
   def __init__(self, addr, port=I2CBUS):
      self.addr = addr
      self.bus = smbus.SMBus(port)

# Write a single command
   def write_cmd(self, cmd):
      self.bus.write_byte(self.addr, cmd)
      sleep(0.0001)

# Write a command and argument
   def write_cmd_arg(self, cmd, data):
      self.bus.write_byte_data(self.addr, cmd, data)
      sleep(0.0001)

# Write a block of data
   def write_block_data(self, cmd, data):
      self.bus.write_block_data(self.addr, cmd, data)
      sleep(0.0001)

# Read a single byte
   def read(self):
      return self.bus.read_byte(self.addr)

# Read
   def read_data(self, cmd):
      return self.bus.read_byte_data(self.addr, cmd)

# Read a block of data
   def read_block_data(self, cmd):
      return self.bus.read_block_data(self.addr, cmd)


# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100 # Enable bit
Rw = 0b00000010 # Read/Write bit
Rs = 0b00000001 # Register select bit

class lcd:
   #initializes objects and lcd
   def __init__(self):
      self.lcd_device = i2c_device(ADDRESS)

      self.lcd_write(0x03)
      self.lcd_write(0x03)
      self.lcd_write(0x03)
      self.lcd_write(0x02)

      self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
      self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
      self.lcd_write(LCD_CLEARDISPLAY)
      self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
      sleep(0.2)


   # clocks EN to latch command
   def lcd_strobe(self, data):
      self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
      sleep(.0005)
      self.lcd_device.write_cmd(((data & ~En) | LCD_BACKLIGHT))
      sleep(.0001)

   def lcd_write_four_bits(self, data):
      self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
      self.lcd_strobe(data)

   # write a command to lcd
   def lcd_write(self, cmd, mode=0):
      self.lcd_write_four_bits(mode | (cmd & 0xF0))
      self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

   # write a character to lcd (or character rom) 0x09: backlight | RS=DR<
   # works!
   def lcd_write_char(self, charvalue, mode=1):
      self.lcd_write_four_bits(mode | (charvalue & 0xF0))
      self.lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))
  
   # put string function with optional char positioning
   def lcd_display_string(self, string, line=1, pos=0):
    pos_new = pos
    if line == 1:
      pos_new = pos
    elif line == 2:
      pos_new = 0x40 + pos
    elif line == 3:
      pos_new = 0x14 + pos
    elif line == 4:
      pos_new = 0x54 + pos

    self.lcd_write(0x80 + pos_new)

    for char in string:
      self.lcd_write(ord(char), Rs)

   # clear lcd and set to home
   def lcd_clear(self):
      self.lcd_write(LCD_CLEARDISPLAY)
      self.lcd_write(LCD_RETURNHOME)

   # define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)
   def backlight(self, state): # for state, 1 = on, 0 = off
      if state == 1:
         self.lcd_device.write_cmd(LCD_BACKLIGHT)
      elif state == 0:
         self.lcd_device.write_cmd(LCD_NOBACKLIGHT)

   # add custom characters (0 - 7)
   def lcd_load_custom_chars(self, fontdata):
      self.lcd_write(0x40);
      for char in fontdata:
         for line in char:
            self.lcd_write_char(line)         




# Source: https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# hostname 10.201.23.91

mylcd = lcd()

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



def get_lcd_frame(list_lines: list[str]) -> np.ndarray:
    '''Create a frame that simulates a 4x20 character LCD screen.'''
    rows, cols = 4, 20

    # Keep only the first four lines and truncate each line to 20 chars.
    lines = [line[:cols] for line in list_lines[:rows]]

    # Pad missing lines with blanks.
    while len(lines) < rows:
        lines.append("")

    # LCD-like colors in BGR.
    # BGR colors: blue background, white active text pixels.
    background = (255, 0, 0)      # blue LCD background
    #pixel_off = (255, 80, 80)     # faint unlit pixel, slightly lighter blue
    pixel_off = background
    pixel_on = (255, 255, 255)    # white active text pixel

    scale = 6
    char_w, char_h = 5, 7
    gap = 1

    cell_w = char_w * scale
    cell_h = char_h * scale

    margin = 14
    width = margin * 2 + cols * cell_w + (cols - 1) * gap * scale
    height = margin * 2 + rows * cell_h + (rows - 1) * gap * scale

    frame = np.full((height, width, 3), background, dtype=np.uint8)

    font = {
        " ": ["00000"] * 7,
        "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
        "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
        "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
        "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
        "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
        "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
        "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
        "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
        "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
        "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
        "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
        "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
        "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
        "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
        "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
        "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
        "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
        "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
        "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
        "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
        "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
        "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
        "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
        "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
        "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
        "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
        "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
        "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
        "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
        "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
        "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
        "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
        "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
        "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
        "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
        "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
        ".": ["00000", "00000", "00000", "00000", "00000", "00110", "00110"],
        ",": ["00000", "00000", "00000", "00000", "00110", "00100", "01000"],
        ":": ["00000", "00110", "00110", "00000", "00110", "00110", "00000"],
        "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
        "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
        "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
        "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
        "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
        "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
        "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
        "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
        "*": ["00000", "10101", "01110", "11111", "01110", "10101", "00000"],
        "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
        ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
        "<": ["00010", "00100", "01000", "10000", "01000", "00100", "00010"],
        ">": ["01000", "00100", "00010", "00001", "00010", "00100", "01000"],
    }

    def draw_char(ch: str, x0: int, y0: int) -> None:
        glyph = font.get(ch.upper(), font["?"])

        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                color = pixel_on if bit == "1" else pixel_off
                x = x0 + col * scale
                y = y0 + row * scale
                frame[y:y + scale, x:x + scale] = color

    for line_index, text in enumerate(lines):
        for char_index, ch in enumerate(text):
            x = margin + char_index * (cell_w + gap * scale)
            y = margin + line_index * (cell_h + gap * scale)
            draw_char(ch, x, y)

    return frame


def get_lcd_frame_fieldstate(fieldstate: FieldState) -> np.ndarray:
    '''get the lcd frame with text from a given fieldstate'''

    status_ball = "???"
    # or X,Y so either way 3 char
    if fieldstate.ball_is_seen:
        status_ball = f"{round(fieldstate.ball_pos_in.x)},{round(fieldstate.ball_pos_in.y)}"

    status_opponent ="???"
    if fieldstate.their_bot_is_seen:
        status_opponent = f"{round(fieldstate.their_bot_pos_in.x)},{round(fieldstate.their_bot_pos_in.y)}"

    status_us = f"{round(fieldstate.our_bot_pos_in.x)},{round(fieldstate.our_bot_pos_in.y)}"
    command_us = f"{fieldstate.our_bot_command}"


    row1 = f"us {command_us}"
    row2 = f"bl {status_ball}"
    row3 = f"op {status_opponent}"
    row4 = f"cm {command_us}"


    list_lines = [row1, row2, row3, row4]

    lcd_frame = get_lcd_frame(list_lines= list_lines)
    return lcd_frame


