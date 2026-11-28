"""
BotCommand dataclass + serial sender for the Arduino Mega mecanum robot sketch (robot_test_v6.ino).

Requires: pip install pyserial

Wire formats (newline-terminated, 115200 baud):
    MOTOR   <LF|RF|LB|RB|ALL>_<speed%>_<seconds>     e.g. LF_100_10
    STRAFE  STRAFE_<speed%>_<angle>[_<seconds>]       e.g. STRAFE_50_90   (angle +CCW from east)
    ROTATE  ROTATE_<speed%>_<degrees>[_<seconds>]     e.g. ROTATE_60_90   (+CCW)
    STOP    STOP
    TEST    TEST

Run this file directly for an interactive prompt (type ? at any prompt for help).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

import serial  # pyserial

VALID_MOTORS = ("LF", "RF", "LB", "RB", "ALL")


def _fmt(x: float) -> str:
    """Format a number compactly: 100.0 -> '100', 2.5 -> '2.5'."""
    return f"{x:g}"


@dataclass
class BotCommand:
    """
    One command for the robot.

    kind     : "MOTOR", "STRAFE", "ROTATE", "STOP", or "TEST"
    motor    : "LF", "RF", "LB", "RB" or "ALL" (MOTOR only)
    speed    : percent. MOTOR: -100..100 (negative = reverse). STRAFE/ROTATE: 0..100
    angle    : STRAFE: degrees +CCW from east (90 = forward).
               ROTATE: degrees, positive = CCW, negative = CW
    seconds  : run time. Required for MOTOR. Optional for STRAFE (omitted = until STOP)
               and ROTATE (omitted = firmware estimates time from degrees).
    """
    kind: str
    motor: Optional[str] = None
    speed: float = 0.0
    angle: float = 0.0
    seconds: Optional[float] = None

    # ---- convenience constructors ----
    @classmethod
    def motor_cmd(cls, motor: str, speed: float, seconds: float) -> "BotCommand":
        return cls(kind="MOTOR", motor=motor, speed=speed, seconds=seconds)

    @classmethod
    def strafe(cls, speed: float, angle: float, seconds: Optional[float] = None) -> "BotCommand":
        return cls(kind="STRAFE", speed=speed, angle=angle, seconds=seconds)

    @classmethod
    def rotate(cls, speed: float, degrees: float, seconds: Optional[float] = None) -> "BotCommand":
        return cls(kind="ROTATE", speed=speed, angle=degrees, seconds=seconds)

    @classmethod
    def stop(cls) -> "BotCommand":
        return cls(kind="STOP")

    @classmethod
    def test(cls) -> "BotCommand":
        return cls(kind="TEST")

    # ---- validation ----
    def __post_init__(self) -> None:
        self.kind = self.kind.upper()
        if self.motor is not None:
            self.motor = self.motor.upper()

        if self.kind == "MOTOR":
            if self.motor not in VALID_MOTORS:
                raise ValueError(f"motor must be one of {VALID_MOTORS}, got {self.motor!r}")
            if not -100 <= self.speed <= 100:
                raise ValueError("MOTOR speed must be between -100 and 100")
            if self.seconds is None or self.seconds <= 0:
                raise ValueError("MOTOR requires seconds > 0")

        elif self.kind == "STRAFE":
            if not 0 <= self.speed <= 100:
                raise ValueError("STRAFE speed must be between 0 and 100")
            if self.seconds is not None and self.seconds <= 0:
                raise ValueError("seconds must be > 0 (or None for until STOP)")

        elif self.kind == "ROTATE":
            if not 0 < self.speed <= 100:
                raise ValueError("ROTATE speed must be between 0 (exclusive) and 100")
            if self.angle == 0:
                raise ValueError("ROTATE degrees must be non-zero")
            if self.seconds is not None and self.seconds <= 0:
                raise ValueError("seconds must be > 0 (or None to estimate from degrees)")

        elif self.kind in ("STOP", "TEST"):
            pass

        else:
            raise ValueError(f"Unknown command kind: {self.kind!r}")

    # ---- serialization ----
    def to_wire(self) -> str:
        """Return the command string WITHOUT the trailing newline."""
        if self.kind == "MOTOR":
            return f"{self.motor}_{_fmt(self.speed)}_{_fmt(self.seconds)}"

        if self.kind in ("STRAFE", "ROTATE"):
            parts = [self.kind, _fmt(self.speed), _fmt(self.angle)]
            if self.seconds is not None:
                parts.append(_fmt(self.seconds))
            return "_".join(parts)

        return self.kind  # STOP / TEST


def open_bot_serial(port: str, baud: int = 115200, boot_wait: float = 2.0) -> serial.Serial:
    """
    Open the serial port. Opening it resets an Arduino Mega, so wait for it to boot
    and discard the startup banner.
    """
    ser = serial.Serial(port, baud, timeout=0.2)
    time.sleep(boot_wait)
    ser.reset_input_buffer()
    return ser


def send_command(
    ser: serial.Serial,
    cmd: BotCommand,
    read_reply: bool = True,
    reply_timeout: float = 0.5,
) -> List[str]:
    """
    Send a BotCommand to the Arduino, newline-terminated.

    If read_reply is True, collect the lines the Arduino prints back until it has been
    quiet for reply_timeout seconds, and return them (empty list if none).
    """
    line = cmd.to_wire() + "\n"
    ser.write(line.encode("ascii"))
    ser.flush()

    replies: List[str] = []
    if read_reply:
        last_rx = time.monotonic()
        while time.monotonic() - last_rx < reply_timeout:
            raw = ser.readline()
            if raw:
                replies.append(raw.decode("ascii", errors="replace").strip())
                last_rx = time.monotonic()
    return replies


# ---------------------------------------------------------------------------
# Interactive prompting
# ---------------------------------------------------------------------------

MENU_HELP = """
Commands:
  1  motor   Run one wheel (or ALL) at a set speed for a set time
  2  strafe  Drive in any direction (mecanum). Angle is +CCW from east:
               0 = right, 90 = forward, 180 = left, 270 = back
  3  rotate  Spin in place. Positive degrees = CCW, negative = CW
  4  stop    Brake all motors immediately
  5  test    Run the built-in automatic motor test sequence
  q  quit    Exit

Type ? at any prompt to see help for that prompt.
"""


def _ask_float(
    prompt: str,
    help_text: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    optional: bool = False,
    nonzero: bool = False,
    min_exclusive: bool = False,
) -> Optional[float]:
    """Ask for a number, re-prompting until valid. '?' shows help; blank returns None if optional."""
    while True:
        raw = input(f"{prompt}{' (optional, Enter to skip)' if optional else ''}: ").strip()

        if raw == "?":
            print(f"  {help_text}")
            continue
        if raw == "" and optional:
            return None

        try:
            value = float(raw)
        except ValueError:
            print("  Please enter a number (or ? for help).")
            continue

        if nonzero and value == 0:
            print("  Value cannot be zero.")
        elif min_val is not None and (value < min_val or (min_exclusive and value == min_val)):
            print(f"  Value must be {'greater than' if min_exclusive else 'at least'} {_fmt(min_val)}.")
        elif max_val is not None and value > max_val:
            print(f"  Value must be at most {_fmt(max_val)}.")
        else:
            return value


def _ask_motor() -> str:
    while True:
        raw = input("Motor [LF/RF/LB/RB/ALL]: ").strip().upper()
        if raw == "?":
            print("  LF = left front, RF = right front, LB = left back, RB = right back, "
                  "ALL = all four at once.")
        elif raw in VALID_MOTORS:
            return raw
        else:
            print(f"  Choose one of {', '.join(VALID_MOTORS)} (or ? for help).")


def prompt_for_command() -> Optional[BotCommand]:
    """
    Interactively build a BotCommand, with help text at every step.
    Returns None if the user chooses to quit.
    """
    print(MENU_HELP)
    while True:
        choice = input("Command [1-5, q, ?]: ").strip().lower()

        if choice in ("?", "h", "help"):
            print(MENU_HELP)

        elif choice in ("q", "quit", "exit"):
            return None

        elif choice in ("1", "motor"):
            motor = _ask_motor()
            speed = _ask_float(
                "Speed % (-100 to 100)",
                "Percent of full power. Negative runs the motor in reverse.",
                -100, 100)
            seconds = _ask_float(
                "Seconds",
                "How long to run, in seconds. Decimals allowed (e.g. 2.5).",
                0, None, min_exclusive=True)
            return BotCommand.motor_cmd(motor, speed, seconds)

        elif choice in ("2", "strafe"):
            speed = _ask_float(
                "Speed % (0 to 100)",
                "Duty of the fastest wheel; the others are scaled to match.",
                0, 100)
            angle = _ask_float(
                "Angle in degrees",
                "Direction of travel, +CCW from the robot's east (right): "
                "0 = right, 90 = forward, 180 = left, 270 = back. Any angle works, e.g. 45.")
            seconds = _ask_float(
                "Seconds",
                "How long to strafe. Skip to keep going until you send STOP.",
                0, None, optional=True, min_exclusive=True)
            return BotCommand.strafe(speed, angle, seconds)

        elif choice in ("3", "rotate"):
            speed = _ask_float(
                "Speed % (greater than 0, up to 100)",
                "Duty applied to every wheel while spinning.",
                0, 100, min_exclusive=True)
            degrees = _ask_float(
                "Degrees (+CCW, -CW)",
                "Sign sets the direction: positive = counterclockwise, negative = clockwise. "
                "If you give seconds, only the sign is used; if you skip seconds, the "
                "firmware estimates run time from the size of this number.",
                nonzero=True)
            seconds = _ask_float(
                "Seconds",
                "How long to spin. Skip to let the robot estimate the time from the degrees.",
                0, None, optional=True, min_exclusive=True)
            return BotCommand.rotate(speed, degrees, seconds)

        elif choice in ("4", "stop"):
            return BotCommand.stop()

        elif choice in ("5", "test"):
            return BotCommand.test()

        else:
            print("  Unrecognized choice. Enter 1-5, q to quit, or ? for help.")


if __name__ == "__main__":
    # Change the port for your system (e.g. "COM3" on Windows,
    # "/dev/ttyACM0" on Linux, "/dev/cu.usbmodem1101" on macOS).
    PORT = "/dev/ttyACM0"

    with open_bot_serial(PORT) as bot:
        try:
            while True:
                command = prompt_for_command()
                if command is None:
                    break
                print(">>", command.to_wire())
                for reply in send_command(bot, command):
                    print("<<", reply)
                print()
        except (KeyboardInterrupt, EOFError):
            print()
        finally:
            # Make sure the robot isn't left driving when the script exits
            send_command(bot, BotCommand.stop(), read_reply=False)
            print("Sent STOP. Goodbye.")