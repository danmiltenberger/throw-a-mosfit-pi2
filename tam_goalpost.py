from dataclasses import dataclass, field
from tam_classes import Point, CameraState
from tam_constants import CAMERA_CAPTURE_X  # 1280
import math

# For reference
# FIELD_SOUTHWEST_CORNER = Point(0,0)
# FIELD_SOUTHEAST_CORNER = Point(96,0)
# FIELD_NORTHWEST_CORNER = Point(0,144)
# FIELD_NORTHEAST_CORNER = Point(96,144)

GOALPOST_SOUTHWEST = Point(24,0)
GOALPOST_SOUTHEAST = Point(72,0)
GOALPOST_NORTHWEST = Point(24,144)
GOALPOST_NORTHEAST = Point(72,144)

HFOV_RAD = math.radians(62.2)
BASELINE_IN = 10              # distance between the two cameras
MIN_DISPARITY_PX = 1.0          # ignore matches with (near) zero disparity -> infinite depth
FOCAL_PX = (CAMERA_CAPTURE_X / 2) / math.tan(HFOV_RAD / 2)
CX = CAMERA_CAPTURE_X / 2


@dataclass
class GoalPost:
    known_point_on_field : Point = field(default_factory=lambda: Point(0, 0))
    pos_on_frame_px : Point = field(default_factory=lambda: Point(0, 0))


@dataclass 
class TotalGoalPost:

    # each goal has two green markers and two purple markers. Distance from green to purple is 48 inches
    left_green_up : GoalPost  = field(default_factory=lambda: GoalPost())
    left_green_down : GoalPost  = field(default_factory=lambda: GoalPost())

    left_purple_up : GoalPost  = field(default_factory=lambda: GoalPost())
    left_purple_down : GoalPost  = field(default_factory=lambda: GoalPost())

    # the points are gathered from two picams that both face forward with a 62.2deg hfov and are 5 inches apart
    right_green_up : GoalPost  = field(default_factory=lambda: GoalPost())
    right_green_down : GoalPost  = field(default_factory=lambda: GoalPost())

    right_purple_up : GoalPost  = field(default_factory=lambda: GoalPost())
    right_purple_down : GoalPost  = field(default_factory=lambda: GoalPost())





def _triangulate(left_px: Point, right_px: Point):
    """Return (forward, left) offset in inches of a marker in the robot frame
    (origin = midpoint between cameras), or None if unusable."""
    # (0,0) is the dataclass default, so treat it as "not seen"
    if (left_px.x == 0 and left_px.y == 0) or (right_px.x == 0 and right_px.y == 0):
        return None

    disparity = left_px.x - right_px.x      # nearer objects appear further right in the left cam
    if disparity < MIN_DISPARITY_PX:
        return None

    depth = FOCAL_PX * BASELINE_IN / disparity          # forward distance
    # lateral offset from each camera's axis (+ = right), converted to "+ = left" robot frame
    left_cam_lat = -(left_px.x - CX) * depth / FOCAL_PX + BASELINE_IN / 2
    right_cam_lat = -(right_px.x - CX) * depth / FOCAL_PX - BASELINE_IN / 2
    return depth, (left_cam_lat + right_cam_lat) / 2


def get_bot_pose_from_goalposts(tgp: TotalGoalPost) -> tuple[Point, float]:
    '''from the pixel positions of the goalposts and the known goalpost points, return the bot's position and angle (radians +ccw field east)'''
    pairs = [
        (tgp.left_green_up,   tgp.right_green_up),
        (tgp.left_green_down, tgp.right_green_down),
        (tgp.left_purple_up,  tgp.right_purple_up),
        (tgp.left_purple_down, tgp.right_purple_down),
    ]

    a, k = [], []   # robot-frame offsets, and matching known field points
    for l, r in pairs:
        rel = _triangulate(l.pos_on_frame_px, r.pos_on_frame_px)
        if rel is None:
            continue
        a.append(rel)
        k.append((l.known_point_on_field.x, l.known_point_on_field.y))

    if len(a) < 2:
        raise ValueError("Need at least two valid stereo sightings")

    n = len(a)
    a_mean = (sum(p[0] for p in a) / n, sum(p[1] for p in a) / n)
    k_mean = (sum(p[0] for p in k) / n, sum(p[1] for p in k) / n)

    # Kabsch/Procrustes in 2D: best rotation robot frame -> field frame
    dot = cross = 0.0
    for (ax, ay), (kx, ky) in zip(a, k):
        ax -= a_mean[0]; ay -= a_mean[1]
        kx -= k_mean[0]; ky -= k_mean[1]
        dot += ax * kx + ay * ky
        cross += ax * ky - ay * kx

    if abs(dot) < 1e-9 and abs(cross) < 1e-9:
        raise ValueError("Sightings must include at least two distinct goalposts")

    theta = math.atan2(cross, dot)
    c, s = math.cos(theta), math.sin(theta)

    x = k_mean[0] - (c * a_mean[0] - s * a_mean[1])
    y = k_mean[1] - (s * a_mean[0] + c * a_mean[1])
    return Point(x, y), theta


import math
from dataclasses import dataclass
from tam_classes import Point

FIELD_MARGIN_IN = 12   # reject poses further than this outside the field walls


def build_total_goalpost(
        left_cs: CameraState,
        right_cs: CameraState,
        our_left_is_green: bool = True,
        ) -> TotalGoalPost | None:
    '''Field frame: our goal is south (y=0), their goal is north (y=144).
    our_left_is_green: our goal's west post is green (their goal's west post is purple).
    Returns None if no usable goal view exists. Never raises.

    A color is only included if BOTH its up and down markers are visible in BOTH
    cameras. Otherwise a lone marker could be labeled "up" in one camera and "down"
    in the other, and the stereo match would pair two different physical markers.'''

    sees_ours = left_cs.our_goal_in_frame or right_cs.our_goal_in_frame
    sees_theirs = left_cs.their_goal_in_frame or right_cs.their_goal_in_frame

    if sees_ours == sees_theirs:     # neither goal, or ambiguous (both)
        return None

    if sees_ours:
        west_post, east_post = GOALPOST_SOUTHWEST, GOALPOST_SOUTHEAST
    else:
        west_post, east_post = GOALPOST_NORTHWEST, GOALPOST_NORTHEAST
    west_is_green = our_left_is_green   # same painting on both goals in the map frame

    green_post, purple_post = (west_post, east_post) if west_is_green else (east_post, west_post)

    # (color, known point, up in_frame attr, up pos attr, down in_frame attr, down pos attr)
    colors = [
        ("green",  green_post,  "gp_green_up_in_frame", "gp_green_up_pos_px",
                                "gp_green_dw_in_frame", "gp_green_dw_pos_px"),
        ("purple", purple_post, "gp_purpl_up_in_frame", "gp_purpl_up_pos_px",
                                "gp_purpl_dw_in_frame", "gp_purpl_dw_pos_px"),
    ]

    tgp = TotalGoalPost()
    any_color_used = False

    for color, known, up_in, up_pos, dw_in, dw_pos in colors:
        both_cams_see_both = all(
            getattr(cs, up_in) and getattr(cs, dw_in) for cs in (left_cs, right_cs)
        )
        if not both_cams_see_both:
            continue    # skip this color entirely; its pixels stay at the (0, 0) "not seen" default

        for side, cs in (("left", left_cs), ("right", right_cs)):
            for suffix, in_attr, pos_attr in (("up", up_in, up_pos), ("down", dw_in, dw_pos)):
                gp: GoalPost = getattr(tgp, f"{side}_{color}_{suffix}")
                gp.known_point_on_field = known
                gp.pos_on_frame_px = getattr(cs, pos_attr)
        any_color_used = True

    return tgp if any_color_used else None


class PoseTracker:
    '''Holds the last good bot pose. update() never raises: on any failure it
    returns the previous pose and sets last_update_ok = False.'''

    def __init__(self, initial_pos: Point = Point(48, 0), initial_heading_rad: float = math.pi / 2):
        # initial values are a guess (center of our goal line, facing north): set to your start pose
        self.pos = initial_pos
        self.heading_rad = initial_heading_rad
        self.last_update_ok = False
        self.frames_since_fix = 0

    def update(self, left_cs: CameraState, right_cs: CameraState,
               our_left_is_green: bool = True) -> tuple[Point, float]:
        try:
            tgp = build_total_goalpost(left_cs, right_cs, our_left_is_green)
            if tgp is None:
                raise ValueError("no usable goal view")

            pos, heading = get_bot_pose_from_goalposts(tgp)

            if not (math.isfinite(pos.x) and math.isfinite(pos.y) and math.isfinite(heading)):
                raise ValueError("non-finite pose")
            if not (-FIELD_MARGIN_IN <= pos.x <= 96 + FIELD_MARGIN_IN and
                    -FIELD_MARGIN_IN <= pos.y <= 144 + FIELD_MARGIN_IN):
                raise ValueError("pose outside field")

        except Exception:
            # includes the ValueErrors from the pose solve (too few / non-distinct sightings)
            self.last_update_ok = False
            self.frames_since_fix += 1
            return self.pos, self.heading_rad

        self.pos, self.heading_rad = pos, heading
        self.last_update_ok = True
        self.frames_since_fix = 0
        return self.pos, self.heading_rad