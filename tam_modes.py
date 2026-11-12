# THIS IS ALL AI AND NEEDS A LOOK THROUGH
# NOT READY RIGHT NOW



"""
Simple state machine ("modes") for the soccer bot.

HOW IT WORKS
------------
- The robot is always in exactly ONE mode (stored in Brain.mode).
- Every frame, main loop calls brain.step(fieldstate).
- step() runs the function for the CURRENT mode only.
- A mode function returns two things:
      1. the BotCommand to send right now
      2. the mode to be in next frame (return its own mode to stay)

TO ADD A NEW MODE
-----------------
  1. Add a name to the Mode enum.
  2. Write a function  def mode_xxx(brain, fs) -> tuple[BotCommand, Mode]
  3. Add it to MODE_FUNCTIONS at the bottom.
  4. Return Mode.XXX from some other mode to enter it.
"""

import math
import time
from enum import Enum, auto
import numpy as np

from tam_classes import Point, FieldState, BotCommand, get_capture_zone_point
from tam_commands import BOT_FORWARD, BOT_BACKWARD, BOT_ROTATE_LEFT, BOT_ROTATE_RIGHT, BOT_KICK, BOT_STRAFE_LEFT, BOT_STRAFE_RIGHT, ARM_OUT
from tam_points import FIELD_GOAL_CENTER_TOP, FIELD_GOALBOX_CENTER_BOTTOM
from tam_constants import BEARING_EAST, BEARING_NORTH
from tam_points import FIELD_GOAL_CENTER_BOTTOM



# ---------------------------------------------------------------------------
# 1. The list of modes
# ---------------------------------------------------------------------------
class Mode(Enum):
    SEARCH = auto()          # spin until we see the ball
    APPROACH_BALL = auto()   # drive to the ball
    DRIBBLE = auto()         # ball is in front of us, push it toward their goal
    SHOOT = auto()           # kick, then go back to searching
    HOME = auto()            # go to the position in front of our goal
    DEFEND = auto()          # Stand between play and goal with arms out -> if oppent no longer as ball -> search
    ORBIT_BALL = auto()      # rotate around the ball to get a better angle on the goal

# ---------------------------------------------------------------------------
# Tuning numbers (all inches / seconds / radians)
# ---------------------------------------------------------------------------
CMD_DUR_SEC = 0.15            # short commands; re-decided every frame
AIM_TOLERANCE_RAD = math.radians(15)
BALL_LOST_FRAMES_MAX = 10     # how many frames without the ball before giving up
SHOOT_RANGE_IN = 30           # kick when this close to their goal
CAPTURE_EXIT_EXTRA_IN = 3     # hysteresis: must be this much farther out to "lose" the ball
SHOOT_COOLDOWN_SEC = 1.0      # time to stay in SHOOT after kicking
DEFEND_EXIT_FRAMES = 5        # how many frames the opponenet does not have the ball before going after ball


DEFEND_LINE_Y_IN = 12         # y of the line we strafe along to
DEFEND_X_MARGIN_IN = 4        # don't let the guard point get too close to the goalposts
DEFEND_Y_TOL_IN = 1           # how close to the defend line is "good enough"
DEFEND_X_TOL_IN = 1           # how close to the guard point is "good enough"
ARM_TRIGGER_DIST_IN = 12      # if the threat is this close, put arms out
ARM_COOLDOWN_SEC = 1.0        # don't spam the arms out command     
GOALPOST_SOUTHWEST = Point(36, 0)
GOALPOST_SOUTHEAST = Point(60, 0)

ORBIT_RADIUS_IN = 14          # bot center -> ball center while orbiting (capture zone is 10" ahead, +4" clearance)
ORBIT_RADIUS_TOL_IN = 2
ORBIT_ANGLE_TOL_RAD = math.radians(15)  # "behind the ball" is good enough within this
FACE_BALL_TOL_RAD = math.radians(15)
ORBIT_STRAFE_SEC = 0.3        # strafe is slow, so use longer steps





# ---------------------------------------------------------------------------
# 2. The Brain: holds the current mode + anything that needs memory between frames
# ---------------------------------------------------------------------------
class Brain:
    def __init__(self, start_mode: Mode = Mode.SEARCH):
        self.mode = start_mode
        self.mode_start_time = time.perf_counter()
        self.ball_lost_frames = 0
        self.has_kicked = False
        self.not_theirs_frames = 0
    def time_in_mode(self) -> float:
        return time.perf_counter() - self.mode_start_time

    def enter_mode(self, new_mode: Mode):
        """Switch modes. This is the ONLY place the mode changes."""

        if new_mode == self.mode:
            return
        print(f"[MODE] {self.mode.name} -> {new_mode.name}")
        self.mode = new_mode
        self.mode_start_time = time.perf_counter()

        # reset per-mode memory on entry
        self.ball_lost_frames = 0
        self.has_kicked = False

    def step(self, fs: FieldState) -> BotCommand:
        """Call once per frame. Returns the command to send."""

        # bookkeeping shared by every mode
        if fs.ball_is_seen:
            self.ball_lost_frames = 0
        else:
            self.ball_lost_frames += 1

        mode_function = MODE_FUNCTIONS[self.mode]
        command, next_mode = mode_function(self, fs)
        self.enter_mode(next_mode)
        return command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def distance(a: Point, b: Point) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)

def wrap_angle(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi

def angle_error_to(fs: FieldState, target: Point) -> float:
    """Signed angle (rad) from our heading to the target. + = target is to the left."""

    target_bearing = math.atan2(target.y - fs.our_bot_pos_in.y, target.x - fs.our_bot_pos_in.x)
    return (target_bearing - fs.our_bot_bearing_rad + math.pi) % (2 * math.pi) - math.pi

def rotate_around_ball(fs: FieldState, goal: Point = FIELD_GOAL_CENTER_TOP) -> tuple[BotCommand, bool]:
    '''Rotate around the ball to get a better angle on the goal, in a semicircle around the ball
    (7in diameter). Keeps facing the ball and strafes sideways around it.
    Returns (command, done). done = True when we're behind the ball, lined up with the goal.'''

    ball = fs.ball_pos_in
    bot = fs.our_bot_pos_in

    # where we are around the ball, and where we want to be (directly opposite the goal)
    angle_now = math.atan2(bot.y - ball.y, bot.x - ball.x)
    angle_want = math.atan2(ball.y - goal.y, ball.x - goal.x)
    orbit_err = wrap_angle(angle_want - angle_now)   # + = need to go counterclockwise

    # 1. keep facing the ball
    face_err = angle_error_to(fs, ball)
    if face_err > FACE_BALL_TOL_RAD:
        return BotCommand(BOT_ROTATE_LEFT, CMD_DUR_SEC), False
    if face_err < -FACE_BALL_TOL_RAD:
        return BotCommand(BOT_ROTATE_RIGHT, CMD_DUR_SEC), False

    # 2. stay on the circle (strafing in a straight line drifts outward)
    radius_err = distance(bot, ball) - ORBIT_RADIUS_IN
    if radius_err > ORBIT_RADIUS_TOL_IN:
        return BotCommand(BOT_FORWARD, CMD_DUR_SEC), False
    if radius_err < -ORBIT_RADIUS_TOL_IN:
        return BotCommand(BOT_BACKWARD, CMD_DUR_SEC), False

    # 3. done?
    if abs(orbit_err) < ORBIT_ANGLE_TOL_RAD:
        return BotCommand(), True

    # 4. strafe around. Facing the ball: right = counterclockwise around it, left = clockwise
    if orbit_err > 0:
        return BotCommand(BOT_STRAFE_RIGHT, ORBIT_STRAFE_SEC), False
    return BotCommand(BOT_STRAFE_LEFT, ORBIT_STRAFE_SEC), False

def drive_toward(fs: FieldState, target: Point) -> BotCommand: # BOT_FORWARD, BOT_ROTATE_LEFT, BOT_ROTATE_RIGHT
    """Turn if we're not pointed at the target, otherwise drive forward."""

    err = angle_error_to(fs, target)
    if err > AIM_TOLERANCE_RAD:
        return BotCommand(BOT_ROTATE_LEFT, CMD_DUR_SEC)
    if err < -AIM_TOLERANCE_RAD:
        return BotCommand(BOT_ROTATE_RIGHT, CMD_DUR_SEC)
    return BotCommand(BOT_FORWARD, CMD_DUR_SEC)

def ball_in_capture_zone(fs: FieldState, extra_radius_in: float = 0) -> bool:
    fs = get_capture_zone_point(fs)
    return distance(fs.ball_pos_in, fs.capture_zone_center) <= fs.our_bot_capture_zone_radius + extra_radius_in


# ---------------------------------------------------------------------------
# 3. The modes. Each one: decide what to do, and decide whether to leave.
# ---------------------------------------------------------------------------
def mode_search(brain: Brain, fs: FieldState) -> tuple[BotCommand, Mode]:  #APPROACH_BALL, SEARCH
    # EXIT: we see the ball
    if fs.ball_is_seen:
        return BotCommand(), Mode.APPROACH_BALL

    if fs.ball_is_theirs:
        return BotCommand(), Mode.HOME

    # ACTION: spin in place
    return BotCommand(BOT_ROTATE_LEFT, CMD_DUR_SEC), Mode.SEARCH


def mode_approach_ball(brain: Brain, fs: FieldState) -> tuple[BotCommand, Mode]: #HOME, SEARCH, ORBIT_BALL, DRIBBLE, DRIBBLE, APPROACH_BALL
    if fs.ball_is_theirs:
        return BotCommand(), Mode.HOME
    
    if brain.ball_lost_frames > BALL_LOST_FRAMES_MAX:
        return BotCommand(), Mode.SEARCH

    # NEW: close to the ball but on the wrong side -> orbit around it
    near_ball = distance(fs.our_bot_pos_in, fs.ball_pos_in) < ORBIT_RADIUS_IN + 4
    if near_ball and not lined_up(fs, FIELD_GOAL_CENTER_TOP):
        return BotCommand(), Mode.ORBIT_BALL

    if fs.ball_is_seen and ball_in_capture_zone(fs):
        return BotCommand(), Mode.DRIBBLE

    return drive_toward(fs, fs.ball_pos_in), Mode.APPROACH_BALL


def mode_dribble(brain: Brain, fs: FieldState) -> tuple[BotCommand, Mode]: #APPROACH_BALL, SHOOT, DRIBBLE
    # EXIT: ball got away (note the bigger radius = hysteresis, prevents flicker)

    if brain.ball_lost_frames > BALL_LOST_FRAMES_MAX or (
        fs.ball_is_seen and not ball_in_capture_zone(fs, extra_radius_in=CAPTURE_EXIT_EXTRA_IN)
    ):
        return BotCommand(), Mode.APPROACH_BALL

    # EXIT: close enough and aimed at their goal -> shoot
    close = distance(fs.our_bot_pos_in, FIELD_GOAL_CENTER_TOP) < SHOOT_RANGE_IN
    aimed = abs(angle_error_to(fs, FIELD_GOAL_CENTER_TOP)) < AIM_TOLERANCE_RAD

    if close and aimed:
        return BotCommand(), Mode.SHOOT

    # ACTION: push toward their goal
    return drive_toward(fs, FIELD_GOAL_CENTER_TOP), Mode.DRIBBLE


def mode_shoot(brain: Brain, fs: FieldState) -> tuple[BotCommand, Mode]: #SHOOT, SEARCH, SHOOT
    # ACTION (once): kick

    if not brain.has_kicked:
        brain.has_kicked = True
        return BotCommand(BOT_KICK, 0), Mode.SHOOT

    # EXIT: after a short cooldown, go find the ball again
    if brain.time_in_mode() > SHOOT_COOLDOWN_SEC:
        return BotCommand(), Mode.SEARCH

    # ACTION: wait (no command) while the kicker retracts
    return BotCommand(), Mode.SHOOT


def mode_home(brain: Brain, fs: FieldState) -> tuple[BotCommand, Mode]: #HOME, DEFEND, APPROACH_BALL
    # ACTION: go to the front of our goal, then sit there
    if not fs.ball_is_theirs and distance(fs.our_bot_pos_in, fs.ball_pos_in) <= 4:
        return BotCommand(), Mode.APPROACH_BALL

    elif distance(fs.our_bot_pos_in, FIELD_GOALBOX_CENTER_BOTTOM) > 4:
        return drive_toward(fs, FIELD_GOALBOX_CENTER_BOTTOM), Mode.HOME
    
    elif distance(fs.our_bot_pos_in, FIELD_GOALBOX_CENTER_BOTTOM) <= 4:
        return BotCommand(), Mode.DEFEND
    
    return BotCommand(), Mode.HOME


def mode_defend(brain: Brain, fs: FieldState) -> tuple[BotCommand, Mode]: #SEARCH, DEFEND
    '''Strafe in front of our goal to defend, in between the opponent and our goal.
    If the opponent lost the ball, go back to searching for the ball.'''

    # EXIT: opponent hasn't had the ball for several frames in a row -> search
    if fs.ball_is_theirs:
        brain.not_theirs_frames = 0
    else:
        brain.not_theirs_frames += 1
    if brain.not_theirs_frames > DEFEND_EXIT_FRAMES:
        return BotCommand(), Mode.SEARCH

    # what we're guarding against: the ball if we see it, otherwise their bot
    threat = fs.ball_pos_in if fs.ball_is_seen else fs.their_bot_pos_in

    # guard point: where the line threat -> our goal center crosses our defend line
    goal = FIELD_GOAL_CENTER_BOTTOM
    if threat.y > goal.y:
        t = (DEFEND_LINE_Y_IN - goal.y) / (threat.y - goal.y)
        guard_x = goal.x + t * (threat.x - goal.x)
    else:
        guard_x = threat.x
    guard_x = max(GOALPOST_SOUTHWEST.x + DEFEND_X_MARGIN_IN,
                  min(GOALPOST_SOUTHEAST.x - DEFEND_X_MARGIN_IN, guard_x))
    guard = Point(guard_x, DEFEND_LINE_Y_IN)

    # ACTION 1: not on the defend line yet -> drive there
    if abs(fs.our_bot_pos_in.y - DEFEND_LINE_Y_IN) > DEFEND_Y_TOL_IN:
        return drive_toward(fs, guard), Mode.DEFEND

    # ACTION 2: face north (toward the play) so strafing moves us along the line
    heading_err = (BEARING_NORTH - fs.our_bot_bearing_rad + math.pi) % (2 * math.pi) - math.pi
    if heading_err > AIM_TOLERANCE_RAD:
        return BotCommand(BOT_ROTATE_LEFT, CMD_DUR_SEC), Mode.DEFEND
    if heading_err < -AIM_TOLERANCE_RAD:
        return BotCommand(BOT_ROTATE_RIGHT, CMD_DUR_SEC), Mode.DEFEND

    # ACTION 3: threat is close -> arms out (with  cooldown so we don't spam it)
    now = time.perf_counter()
    if (distance(fs.our_bot_pos_in, threat) < ARM_TRIGGER_DIST_IN
            and now - brain.arm_last_time > ARM_COOLDOWN_SEC):
        brain.arm_last_time = now
        return BotCommand(ARM_OUT, 0), Mode.DEFEND

    # ACTION 4: strafe to stay between threat and goal (facing north: left = -x, right = +x)
    x_err = guard.x - fs.our_bot_pos_in.x
    if x_err > DEFEND_X_TOL_IN:
        return BotCommand(BOT_STRAFE_RIGHT, CMD_DUR_SEC), Mode.DEFEND
    if x_err < -DEFEND_X_TOL_IN:
        return BotCommand(BOT_STRAFE_LEFT, CMD_DUR_SEC), Mode.DEFEND

    # in position: hold
    return BotCommand(), Mode.DEFEND 


def mode_orbit_ball(brain: Brain, fs: FieldState) -> tuple[BotCommand, Mode]:
    if fs.ball_is_theirs:
        return BotCommand(), Mode.DEFEND
    if brain.ball_lost_frames > BALL_LOST_FRAMES_MAX:
        return BotCommand(), Mode.SEARCH

    command, done = rotate_around_ball(fs, FIELD_GOAL_CENTER_TOP)
    if done:
        return BotCommand(), Mode.APPROACH_BALL   # lined up -> approach drives straight in
    return command, Mode.ORBIT_BALL


# ---------------------------------------------------------------------------
# 4. Lookup table: Mode -> function. Add new modes here.
# ---------------------------------------------------------------------------
MODE_FUNCTIONS = {
    Mode.SEARCH: mode_search,
    Mode.APPROACH_BALL: mode_approach_ball,
    Mode.DRIBBLE: mode_dribble,
    Mode.SHOOT: mode_shoot,
    Mode.HOME: mode_home,
    Mode.DEFEND: mode_defend, 
    Mode.ORBIT_BALL: mode_orbit_ball, 
}


# ---------------------------------------------------------------------------
# Demo: fake field, fake physics, no camera or Arduino needed.
#   python3 tam_modes.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from tam_constants import BEARING_EAST
    from tam_ourbot import in_per_sec_forward, rad_per_sec_rotation

    fs = FieldState()
    fs.our_bot_pos_in = Point(48, 12)
    fs.our_bot_bearing_rad = BEARING_EAST   
    fs.ball_pos_in = Point(48, 72)

    brain = Brain()

    for frame in range(400):
        fs.ball_is_seen = abs(angle_error_to(fs, fs.ball_pos_in)) < math.radians(30)  # fake 60deg camera FOV
        cmd = brain.step(fs)

        # fake physics: apply the command
        dt = cmd.dur_sec
        if cmd.com_str == BOT_ROTATE_LEFT:
            fs.our_bot_bearing_rad += rad_per_sec_rotation * dt
        elif cmd.com_str == BOT_ROTATE_RIGHT:
            fs.our_bot_bearing_rad -= rad_per_sec_rotation * dt
        elif cmd.com_str == BOT_FORWARD:
            step = in_per_sec_forward * dt
            fs.our_bot_pos_in.x += step * math.cos(fs.our_bot_bearing_rad)
            fs.our_bot_pos_in.y += step * math.sin(fs.our_bot_bearing_rad)
            if brain.mode == Mode.DRIBBLE:   # ball gets pushed along
                fs.ball_pos_in.x += step * math.cos(fs.our_bot_bearing_rad)
                fs.ball_pos_in.y += step * math.sin(fs.our_bot_bearing_rad)
        elif cmd.com_str == BOT_KICK:
            print(f"KICK at frame {frame}, bot at {fs.our_bot_pos_in}")
            break