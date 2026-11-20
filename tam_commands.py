from dataclasses import dataclass


# movement constants
BOT_ACTION = "BOT_ACTION"
BOT_ACTION_DURATION_SEC = "BOT_ACTION_DURATION_SEC"


ARDUINO_MAX_DURATION = 3

BOT_FORWARD = "W"
BOT_BACKWARD = "S"
BOT_ROTATE_LEFT = "Q"
BOT_ROTATE_RIGHT = "E"
BOT_STRAFE_LEFT = "A"
BOT_STRAFE_RIGHT = "D"

# ARMS
ARM_OUT = "B"           
ARM_IN = "I"       
BOT_KICK = "K"
SENSOR_STATUS = "P"

@dataclass
class BotCommand:
    com_str : str = BOT_FORWARD
    dur_sec : float = 0
    speed_percent : float = 60

    def __str__(self) -> str:
        return self.com_str + str(round(self.dur_sec,1))