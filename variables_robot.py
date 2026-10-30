import math

### Our robot
in_per_sec_strafe : float = 2
in_per_sec_forward : float = 10
in_per_sec_backward : float = 10
rad_per_sec_rotation : float = math.radians(15)

# movement constants
BOT_ACTION = "BOT_ACTION"
BOT_ACTION_DURATION_SEC = "BOT_ACTION_DURATION_SEC"

BOT_FORWARD = "W"
BOT_BACKWARD = "S"
BOT_ROTATE_LEFT = "Q"
BOT_ROTATE_RIGHT = "E"
BOT_STRAFE_LEFT = "A"
BOT_STRAFE_RIGHT = "D"
ARM_OUT = "B"           # TODO handle all the interesting defend code later
ARM_IN = "I"       # max of 2 sec
BOT_KICK = "K"



#q5.0 w3.1 d5, 

# minimum radius of rotation so we don't lose the ball

# rotate with ball as center of rotation


example_command = "FORWARD_5.0"