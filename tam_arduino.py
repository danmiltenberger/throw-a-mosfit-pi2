"""
BotCommand dataclass + serial sender for the Arduino Mega mecanum robot sketch (robot_test_v6.ino).

Requires: pip install pyserial

Wire formats (newline-terminated, 115200 baud):
    MOTOR   <LF|RF|LB|RB|ALL>_<speed%>_<seconds>     e.g. LF_100_10
    STRAFE  STRAFE_<speed%>_<angle>[_<seconds>]       e.g. STRAFE_50_90   (angle +CCW from east)
    ROTATE  ROTATE_<speed%>_<degrees>[_<seconds>]     e.g. ROTATE_60_90   (+CCW)
    STOP    STOP
    TEST    TEST
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


if __name__ == "__main__":
    # Example usage: change the port for your system (e.g. "COM3" on Windows,
    # "/dev/ttyACM0" on Linux, "/dev/cu.usbmodem1101" on macOS).
    PORT = "/dev/ttyACM0"

    with open_bot_serial(PORT) as bot:
        for command in (
            BotCommand.motor_cmd("LF", 100, 2),     # left front, 100%, 2 s
            BotCommand.strafe(50, 90, 3),           # forward at 50% for 3 s
            BotCommand.rotate(60, -90),             # ~90 deg CW at 60%, estimated time
            BotCommand.stop(),
        ):
            print(">>", command.to_wire())
            for reply in send_command(bot, command):
                print("<<", reply)
            time.sleep(0.5)