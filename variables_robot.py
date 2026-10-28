import math

### Our robot
in_per_sec_strafe : float = 2
in_per_sec_forward : float = 10
in_per_sec_backward : float = 10
rad_per_sec_rotation : float = math.radians(15)

# movement constants
BOT_ACTION = "BOT_ACTION"
BOT_ACTION_DURATION_SEC = "BOT_ACTION_DURATION_SEC"

BOT_FORWARD = "BOT_FORWARD"
BOT_BACKWARD = "BOT_BACKWARD"
BOT_ROTATE_LEFT = "BOT_ROTATE_LEFT"
BOT_ROTATE_RIGHT = "BOT_ROTATE_RIGHT"
BOT_STRAFE_LEFT = "BOT_STRAFE_LEFT"
BOT_STRAFE_RIGHT = "BOT_STRAFE_RIGHT"
ARM_OUT = "ARM_OUT"
ARM_IN = "ARM_IN"       # max of 2 sec
BOT_KICK = ""

# minimum radius of rotation so we don't lose the ball

# rotate with ball as center of rotation


example_command = "BOT_FORWARD_5"