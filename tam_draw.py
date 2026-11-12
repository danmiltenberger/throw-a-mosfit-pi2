import numpy as np
import cv2
from tam_classes import Point, get_point_int_tuple, Rectangle, FieldState, Detection, color_dict, BotCommand
import math
from tam_colors import *
from tam_constants import *
from tam_topdown import calc_angle_from_screen_center, calc_distance_from_bot, convert_to_field
from tam_decide import determine_goalpost_position, get_detection_lines, get_detection_dict
from tam_points import CAMERA_CENTER_BOTTOM, CAMERA_CENTER, FIELD_GOALBOX_CENTER_BOTTOM


PIXELS_PER_INCH = 5

def convert_to_px(inches: float) -> int:
    """Convert inches to pixels using the global scale factor."""
    return int(round(inches * PIXELS_PER_INCH))


### defining the field
playing_field_in_x = 8 * 12
playing_field_in_y = 12 * 12

goal_net_in_x = 48
goal_net_in_y = 12  # deep

goalbox_in_x = 48
goalbox_in_y = 24  # infront of the goal

perim_tape_thickness_in = 2
perim_black_beyond_tape_in = 2
total_buffer_in = perim_tape_thickness_in + perim_black_beyond_tape_in

total_window_in_y = 2 * goal_net_in_y + playing_field_in_y
total_window_in_x = 2 * total_buffer_in + playing_field_in_x

# total window
total_window_px_x = int(total_window_in_x * PIXELS_PER_INCH)
total_window_px_y = int(total_window_in_y * PIXELS_PER_INCH)

field_center_px_x = int(total_window_px_x/ 2)
field_center_px_y = int(total_window_px_y / 2)


# goalbox center is 60 inches up / down from center field
goalbox_center_top_in = (0, 60)
goalbox_center_bot_in = (0, -60)


# draw the goalpost hats

goal_net_px_x = convert_to_px(goal_net_in_x)
goal_net_px_y = convert_to_px(goal_net_in_y)

goalpost_left_offset = field_center_px_x - int(goal_net_px_x/2)
goalpost_top_offset = goal_net_px_y

goalbox_right_offset = total_window_px_x - goalpost_left_offset
goalbox_bottom_offset = total_window_px_y - goalpost_top_offset


GOALPOST_LEFT_TOP = Point(goalpost_left_offset, goalpost_top_offset)
GOALPOST_LEFT_BOTTOM = Point(goalpost_left_offset, goalbox_bottom_offset)
GOALPOST_RIGHT_TOP = Point(goalbox_right_offset, goalpost_top_offset)
GOALPOST_RIGHT_BOTTOM = Point(goalbox_right_offset, goalbox_bottom_offset)


def inches_to_screen(
    point: Point,
    screen_height_px: int = total_window_px_y,
) -> Point:
    """Convert bottom-left inch coordinates to top-left pixel coordinates.

    The inch-frame origin is 4 inches right and 12 inches up from
    the screen's bottom-left corner.
    """
    x_px = (point.x + 4) * PIXELS_PER_INCH
    y_px = screen_height_px - (point.y + 12) * PIXELS_PER_INCH

    return Point(x_px, y_px)


def draw_top_down_arrows(
    field_frame: np.ndarray,
    ref_point_in: Point,
    target_point_in: Point,
    ref_bearing_rad: float,
) -> np.ndarray:
    """
    Draw a right-triangle of arrows from a reference point to a target point.

    Field coordinates:
        - Origin is bottom-left
        - +x is right
        - +y is up
        - Units are inches

    Screen conversion is handled by inches_to_screen().

    Draws:
        - Red horizontal arrow and distance label
        - Blue vertical arrow and distance label
        - Green hypotenuse arrow, distance label, and relative angle label
    """
    if not isinstance(field_frame, np.ndarray):
        raise TypeError(
            f"field_frame must be numpy.ndarray, got {type(field_frame).__name__}"
        )

    if field_frame.ndim != 3 or field_frame.shape[2] != 3:
        raise ValueError(
            f"field_frame must be a 3-channel BGR image, got shape {field_frame.shape}"
        )

    if not isinstance(ref_bearing_rad, (int, float)):
        raise TypeError(
            f"ref_bearing_rad must be a number, got {type(ref_bearing_rad).__name__}"
        )

    dx_in = target_point_in.x - ref_point_in.x
    dy_in = target_point_in.y - ref_point_in.y

    horizontal_distance_in = abs(dx_in)
    vertical_distance_in = abs(dy_in)
    hypotenuse_distance_in = math.hypot(dx_in, dy_in)

    # Angle from the reference bearing to the target, in degrees.
    target_bearing_rad = math.atan2(dy_in, dx_in)
    relative_angle_rad = target_bearing_rad - ref_bearing_rad

    # Normalize to [-180, 180] degrees
    relative_angle_deg = math.degrees(relative_angle_rad)
    relative_angle_deg = (relative_angle_deg + 180.0) % 360.0 - 180.0

    # Convert field-inch coordinates to screen pixel coordinates.
    ref_px = inches_to_screen(ref_point_in)
    target_px = inches_to_screen(target_point_in)

    # Corner completing the right triangle.
    corner_field_point = Point(ref_point_in.x, target_point_in.y)
    corner_px = inches_to_screen(corner_field_point)

    red = (0, 0, 255)       # BGR
    blue = (255, 0, 0)      # BGR
    green = (0, 255, 0)     # BGR
    white = (255, 255, 255) # BGR

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    text_thickness = 1
    line_thickness = 2

    # Horizontal leg: reference -> corner
    cv2.arrowedLine(
        img=field_frame,
        pt1=get_point_int_tuple(ref_px),
        pt2=get_point_int_tuple(corner_px),
        color=red,
        thickness=line_thickness,
        line_type=cv2.LINE_AA,
        tipLength=0.08,
    )

    # Vertical leg: corner -> target
    cv2.arrowedLine(
        img=field_frame,
        pt1=get_point_int_tuple(corner_px),
        pt2 = get_point_int_tuple(target_px),
        color=blue,
        thickness=line_thickness,
        line_type=cv2.LINE_AA,
        tipLength=0.08,
    )

    # Hypotenuse: reference -> target
    cv2.arrowedLine(
        img=field_frame,
        pt1=get_point_int_tuple(ref_px),
        pt2=get_point_int_tuple(target_px),
        color=green,
        thickness=line_thickness,
        line_type=cv2.LINE_AA,
        tipLength=0.08,
    )

    def draw_label(
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int],
        offset: tuple[int, int] = (6, -6),
    ) -> None:
        x = position[0] + offset[0]
        y = position[1] + offset[1]

        (text_w, text_h), baseline = cv2.getTextSize(
            text, font, font_scale, text_thickness
        )

        # Keep labels inside the frame.
        frame_h, frame_w = field_frame.shape[:2]
        x = max(2, min(frame_w - text_w - 2, x))
        y = max(text_h + 2, min(frame_h - baseline - 2, y))

        cv2.putText(
            field_frame,
            text,
            (x, y),
            font,
            font_scale,
            white,
            text_thickness,
            cv2.LINE_AA,
        )

        # Small colored underline helps associate the label with its arrow.
        cv2.line(
            field_frame,
            (x, y + baseline + 2),
            (x + text_w, y + baseline + 2),
            color,
            max(1, text_thickness),
            cv2.LINE_AA,
        )

    # Horizontal distance label, placed near the midpoint of the horizontal leg.
    horizontal_mid = (
        int((ref_px.x + corner_px.x) / 2),
        int((ref_px.y + corner_px.y) / 2),
    )
    draw_label(
        f"{horizontal_distance_in:.1f} in",
        horizontal_mid,
        red,
        offset=(6, -8),
    )

    # Vertical distance label, placed near the midpoint of the vertical leg.
    vertical_mid = (
        int((corner_px.x + target_px.x) / 2),
        int((corner_px.y + target_px.y) / 2),
    )
    draw_label(
        f"{vertical_distance_in:.1f} in",
        vertical_mid,
        blue,
        offset=(8, 0),
    )

    # Hypotenuse distance and relative angle label.
    hypotenuse_mid = (
        int((ref_px.x + target_px.x) / 2),
        int((ref_px.y + target_px.y) / 2),
    )
    draw_label(
        f"{hypotenuse_distance_in:.1f} in, {relative_angle_deg:.1f} deg",
        hypotenuse_mid,
        green,
        offset=(8, -10),
    )

    return field_frame


def draw_arrow_point_to_point(frame: np.ndarray, start: Point, end: Point, color: tuple[int,int,int]= BLACK, is_in_inches: bool = False)-> np.ndarray:

    if is_in_inches:
        start = inches_to_screen(start)
        end = inches_to_screen(end)

    frame = cv2.arrowedLine(
        img=frame,
        pt1=get_point_int_tuple(start),
        pt2=get_point_int_tuple(end),
        color=color,
        thickness=PIXELS_PER_INCH,
        line_type=cv2.LINE_AA,
        tipLength=0.08,
    )

    return frame


def draw_line_point_to_point(frame: np.ndarray, start: Point, end: Point, color: tuple[int,int,int]= BLACK) -> np.ndarray:
    frame = cv2.line(
        img= frame,
        pt1= get_point_int_tuple(start),
        pt2= get_point_int_tuple(end),
        color= color,
        thickness= 1
    )

    return frame



def draw_notched_rectangle(
    image: np.ndarray,
    center_x: int,
    top_y: int,
    width: int,
    height: int,
    base_length: int,
    angle_deg: int,
    color=(255, 255, 255),
    rotation_deg=0.0,
    border_thickness=1,
    opacity: float = 1.0,
) -> np.ndarray:
    """
    Draw a filled, rotated rectangle with a V-notch and black border.

    Parameters
    ----------
    image : np.ndarray
        Destination image; modified in place.
    center_x, top_y : float
        Horizontal center and top edge BEFORE rotation, in pixels.
    width, height : float
        Rectangle dimensions before rotation, in pixels.
    base_length : float
        Width of the triangular opening along the unrotated top edge.
    angle_deg : float
        Interior angle at the bottom tip of the V, in degrees.
    color : tuple or int
        OpenCV BGR fill color, or a scalar for a grayscale image.
    rotation_deg : float
        Rotation about the rectangle's center, in degrees.
        Positive = counterclockwise as viewed on the image.
    border_thickness : int
        Black border width in pixels; must be at least 1.
    opacity : float
        Opacity of both the fill and border, from 0 to 1.
        0 = invisible; 1 = fully opaque.

    Returns
    -------
    np.ndarray
        The modified input image.
    """
    values = (
        center_x, top_y, width, height,
        base_length, angle_deg, rotation_deg,
    )
    if not all(np.isfinite(v) for v in values):
        raise ValueError("All geometry parameters must be finite.")
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive.")
    if not 0 < base_length < width:
        raise ValueError("base_length must be between 0 and width.")
    if not 0 < angle_deg < 180:
        raise ValueError("angle_deg must be between 0 and 180.")
    if (
        not isinstance(border_thickness, (int, np.integer))
        or border_thickness < 1
    ):
        raise ValueError("border_thickness must be a positive integer.")
    if not np.isfinite(opacity) or not 0 <= opacity <= 1:
        raise ValueError("opacity must be a finite number between 0 and 1.")

    notch_depth = (base_length / 2) / np.tan(
        np.deg2rad(angle_deg / 2)
    )
    if notch_depth >= height:
        raise ValueError("The notch must be shallower than the rectangle.")

    if opacity == 0:
        return image

    left = center_x - width / 2
    right = center_x + width / 2
    bottom = top_y + height

    vertices = np.array([
        [left,                       top_y],
        [center_x - base_length / 2,  top_y],
        [center_x,                   top_y + notch_depth],
        [center_x + base_length / 2,  top_y],
        [right,                      top_y],
        [right,                      bottom],
        [left,                       bottom],
    ], dtype=np.float64)

    pivot = (float(center_x), float(top_y + height / 2))
    matrix = cv2.getRotationMatrix2D(
        pivot, float(rotation_deg), 1.0
    )
    rotated_vertices = vertices @ matrix[:, :2].T + matrix[:, 2]

    # Retain subpixel geometry until rasterization.
    shift = 8
    points = np.rint(
        rotated_vertices * (1 << shift)
    ).astype(np.int32)

    # Draw directly when opaque; otherwise draw onto a copy.
    overlay = image if opacity == 1 else image.copy()

    cv2.fillPoly(
        overlay,
        [points],
        color=color,
        lineType=cv2.LINE_AA,
        shift=shift,
    )

    black = 0 if image.ndim == 2 else (0,) * image.shape[2]

    cv2.polylines(
        overlay,
        [points],
        isClosed=True,
        color=black,
        thickness=int(border_thickness),
        lineType=cv2.LINE_AA,
        shift=shift,
    )

    if opacity < 1:
        cv2.addWeighted(
            overlay,
            float(opacity),
            image,
            1.0 - float(opacity),
            0,
            dst=image,
        )

    return image


def draw_robot_to_field(field_frame: np.ndarray, pos_in: Point= FIELD_GOALBOX_CENTER_BOTTOM, bearing_rad: float = BEARING_NORTH, color: tuple[int,int,int]= YELLOW) -> np.ndarray:
    '''draw a robot (notched rectangle) to the field'''

    pos_px = inches_to_screen(pos_in)

    field_frame = draw_notched_rectangle(
        image=field_frame,
        center_x=int(pos_px.x),
        top_y=int(pos_px.y - convert_to_px(BOT_RADIUS_IN)),
        width=convert_to_px(BOT_RADIUS_IN) * 2,
        height=convert_to_px(BOT_RADIUS_IN) * 2,
        base_length=convert_to_px(BALL_RED_RADIUS_IN) * 2,
        angle_deg=90,
        color=color,
        rotation_deg=math.degrees(bearing_rad) -90,
        border_thickness=1,
    )

    return field_frame


def draw_ball_to_field(field_frame: np.ndarray, ball_pos_in: Point, outline_color : tuple[int,int,int] = BLACK) -> np.ndarray:
    ball_pos_px = inches_to_screen(ball_pos_in)
    field_frame = draw_outlined_circle(
            center= ball_pos_px,
            outline_color= outline_color,
            fill_color= RED,
            image= field_frame,
            outline_thickness= 2,
            radius= convert_to_px(BALL_RED_RADIUS_IN)
        )

    return field_frame


def draw_vert_centered_rectangle(
    frame: np.ndarray,
    rectangle: Rectangle,
    y: int = 0,
    color: tuple = WHITE,
    thickness: int = -1,
) -> np.ndarray:
    """Draw a horizontally centered rectangle with a vertical offset.

    y:
        0  = vertically centered
        <0 = above center
        >0 = below center

    Modifies frame in place and returns it.
    The rectangle object's x and y fields are ignored.
    """
    frame_height, frame_width = frame.shape[:2]

    if not (0 < rectangle.width <= frame_width):
        raise ValueError("Rectangle width must be positive and fit in the frame.")
    if not (0 < rectangle.height <= frame_height):
        raise ValueError("Rectangle height must be positive and fit in the frame.")

    x_position = (frame_width - rectangle.width) // 2
    y_position = (frame_height - rectangle.height) // 2 + y

    if y_position < 0 or y_position + rectangle.height > frame_height:
        raise ValueError("Vertical offset places the rectangle outside the frame.")

    cv2.rectangle(
        frame,
        (x_position, y_position, rectangle.width, rectangle.height),
        color,
        thickness,
    )

    return frame


def draw_outlined_circle(
    image: np.ndarray,
    center: Point,
    radius: int,
    fill_color: tuple[int, int, int],
    outline_color: tuple[int, int, int],
    outline_thickness: int = 2,
) -> np.ndarray:
    """Draw a filled, outlined circle in place and return the image.

    Colors use BGR order. Point must expose .x and .y attributes.
    """
    if radius < 0:
        raise ValueError("radius must be non-negative.")
    if outline_thickness < 1:
        raise ValueError("outline_thickness must be at least 1.")

    center_xy = (int(center.x), int(center.y))

    cv2.circle(
        image, center_xy, radius, fill_color,
        thickness=-1, lineType=cv2.LINE_AA,
    )
    cv2.circle(
        image, center_xy, radius, outline_color,
        thickness=outline_thickness, lineType=cv2.LINE_AA,
    )

    return image


def draw_transparent_circle(
    image: np.ndarray,
    circle_center: Point,
    radius: int,
    color: tuple[int, int, int] = (0, 255, 0),
    alpha: float = 0.5,
    thickness: int = -1,
) -> np.ndarray:
    """Return a BGR image with a semi-transparent circle.

    Args:
        image: Input BGR image (not modified).
        center: Circle center as a Point
        radius: Circle radius in pixels.
        color: Circle color as (blue, green, red).
        alpha: Opacity, from 0.0 (invisible) to 1.0 (opaque).
        thickness: -1 for a filled circle; positive values for an outline.
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be between 0.0 and 1.0.")
    if radius < 0:
        raise ValueError("radius must be non-negative.")


    center = get_point_int_tuple(circle_center)

    overlay = image.copy()
    cv2.circle(
        overlay,
        center,
        radius,
        color,
        thickness=thickness,
        lineType=cv2.LINE_AA,
    )

    return cv2.addWeighted(overlay, alpha, image, 1.0 - alpha, 0)


def draw_centered_rectangle(
    frame: np.ndarray,
    rectangle: Rectangle,
    color: tuple = WHITE,
    thickness: int = -1,
) -> np.ndarray:
    """Draw a centered rectangle in place and return the frame.

    The supplied rectangle's x and y are ignored, without modifying the object.
    Use thickness=-1 for a filled rectangle or a positive value for an outline.
    """
    frame_height, frame_width = frame.shape[:2]

    if not (0 < rectangle.width <= frame_width):
        raise ValueError("Rectangle width must be positive and fit in the frame.")
    if not (0 < rectangle.height <= frame_height):
        raise ValueError("Rectangle height must be positive and fit in the frame.")

    x = (frame_width - rectangle.width) // 2
    y = (frame_height - rectangle.height) // 2

    cv2.rectangle(
        frame,
        (x, y, rectangle.width, rectangle.height),
        color,
        thickness,
    )

    return frame


def draw_centered_octagon(
    frame: np.ndarray,
    rectangle: Rectangle,
    chamfer: int,
    y: int = 0,
    color: tuple = WHITE,
    thickness: int = -1,
) -> np.ndarray:
    """Draw a rectangle with four 45-degree chamfered corners.

    chamfer: Distance along each edge from the original corner, in pixels.
    y: Vertical offset from frame center; negative moves up, positive moves down.
    thickness: -1 for filled, or a positive integer for an outline.

    Modifies frame in place and returns it.
    The rectangle object's x and y fields are ignored.
    """
    frame_height, frame_width = frame.shape[:2]
    width = rectangle.width
    height = rectangle.height

    if not (0 < width <= frame_width):
        raise ValueError("Rectangle width must be positive and fit in the frame.")
    if not (0 < height <= frame_height):
        raise ValueError("Rectangle height must be positive and fit in the frame.")

    if not isinstance(chamfer, (int, np.integer)):
        raise TypeError("Chamfer must be an integer number of pixels.")

    # Keep all eight sides nonzero in length.
    if not (0 < 2 * chamfer < min(width - 1, height - 1)):
        raise ValueError(
            "Chamfer must be positive and less than half the shortest "
            "corner-to-corner span."
        )

    if thickness != -1 and thickness <= 0:
        raise ValueError("Thickness must be -1 (filled) or a positive integer.")

    left = (frame_width - width) // 2
    top = (frame_height - height) // 2 + y
    right = left + width - 1
    bottom = top + height - 1

    if top < 0 or bottom >= frame_height:
        raise ValueError("Vertical offset places the octagon outside the frame.")

    # Eight vertices ordered clockwise.
    points = np.array(
        [
            (left + chamfer, top),
            (right - chamfer, top),
            (right, top + chamfer),
            (right, bottom - chamfer),
            (right - chamfer, bottom),
            (left + chamfer, bottom),
            (left, bottom - chamfer),
            (left, top + chamfer),
        ],
        dtype=np.int32,
    ).reshape((-1, 1, 2))

    if thickness == -1:
        cv2.fillPoly(frame, [points], color)
    else:
        cv2.polylines(
            frame,
            [points],
            isClosed=True,
            color=color,
            thickness=thickness,
        )

    return frame


def draw_empty_field(
    is_show_image: bool = False,
    draw_centerpoints: bool = False,
    just_black: bool = False,
    save_image: bool = True,
) -> np.ndarray:

    frame: np.ndarray = np.zeros(
        (total_window_px_y, total_window_px_x, 3), dtype=np.uint8
    )

    # start with a background
    background = Rectangle(width=total_window_px_x, height=total_window_px_y)

    # then the 2'' perim 2'' from the edges

    # this has been updated to have a chamber 1' from the edges
    white_px_x = convert_to_px(perim_tape_thickness_in * 2 + playing_field_in_x)
    white_px_y = convert_to_px(perim_tape_thickness_in * 2 + playing_field_in_y)
    white_perimiter = Rectangle(width=white_px_x, height=white_px_y)

    # then the playing field
    playing_field_px_x = convert_to_px(playing_field_in_x)
    playing_field_px_y = convert_to_px(playing_field_in_y)
    playing_field = Rectangle(
        width=playing_field_px_x,
        height=playing_field_px_y,
    )



    goal_net = Rectangle(width=goal_net_px_x, height=goal_net_px_y)

    goalbox_px_x = convert_to_px(goalbox_in_x)
    goalbox_px_y = convert_to_px(goalbox_in_y)
    goalbox = Rectangle(width=goalbox_px_x, height=goalbox_px_y)

    # BEGIN DRAWING TO SCREEN
    draw_centered_rectangle(frame, background, BLACK)

    if just_black:
        cv2.imwrite("field_black.png", frame)
        return frame

    draw_centered_octagon(
        frame,
        white_perimiter,
        convert_to_px(12),
        color=WHITE,
    )

    draw_centered_octagon(
        frame,
        playing_field,
        convert_to_px(12),
        color=GRAY,
    )

    # draw the goal nets
    goal_net_px_y_half = goal_net_px_y / 2
    goal_net_offset = int(total_window_px_y / 2 - goal_net_px_y_half)
    draw_vert_centered_rectangle(
        frame,
        goal_net,
        goal_net_offset,
        YELLOW,
    )

    draw_vert_centered_rectangle(
        frame,
        goal_net,
        -goal_net_offset,
        CYAN,
    )

    # draw the goal boxes
    goalbox_offset = int(goal_net_offset - goal_net_px_y - goal_net_px_y_half)
    draw_vert_centered_rectangle(
        frame,
        goalbox,
        goalbox_offset,
        LIGHT_GRAY,
    )

    draw_vert_centered_rectangle(
        frame,
        goalbox,
        -goalbox_offset,
        LIGHT_GRAY,
    )


    # draw the goalpost hats
    # left top
    frame = cv2.circle(
        img= frame,
        center= get_point_int_tuple(GOALPOST_LEFT_TOP),
        color= FUCHSIA,
        radius= convert_to_px(GOALPOST_RADIUS_IN),
        thickness= -1,
    )

    # left bottom
    frame = cv2.circle(
        img= frame,
        center= get_point_int_tuple(GOALPOST_LEFT_BOTTOM),
        color= FUCHSIA,
        radius= convert_to_px(GOALPOST_RADIUS_IN),
        thickness= -1,
    )

    # right top
    frame = cv2.circle(
        img= frame,
        center= get_point_int_tuple(GOALPOST_RIGHT_TOP),
        color= GREEN,
        radius= convert_to_px(GOALPOST_RADIUS_IN),
        thickness= -1,
    )

    # right bottom
    frame = cv2.circle(
        img= frame,
        center= get_point_int_tuple(GOALPOST_RIGHT_BOTTOM),
        color= GREEN,
        radius= convert_to_px(GOALPOST_RADIUS_IN),
        thickness= -1,
    )


    if draw_centerpoints:
        centerpoint = Rectangle(
            width=30,
            height=30,
        )

        # draw a box right at the center of the field
        draw_centered_rectangle(frame, centerpoint)

        # and then at the center of the light gray goalboxes
        draw_vert_centered_rectangle(
            frame,
            centerpoint,
            goalbox_offset,
        )

        draw_vert_centered_rectangle(
            frame,
            centerpoint,
            -goalbox_offset,
        )

    if is_show_image:
        cv2.imshow("empty_field", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if save_image:
        cv2.imwrite("field_empty.png", frame)

    return frame


def add_text_top(
    frame: np.ndarray,
    text: str,
    align: str = "LEFT",
) -> np.ndarray:
    """Draw text at the top of a BGR image/frame, aligned left or right."""
    if frame is None:
        raise ValueError("frame must not be None")
    if not text:
        return frame

    alignment = align.upper()
    if alignment not in ("LEFT", "RIGHT"):
        raise ValueError("align must be 'LEFT' or 'RIGHT'")

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    margin = 10
    padding = 4

    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_scale, thickness
    )

    frame_h, frame_w = frame.shape[:2]

    if alignment == "LEFT":
        x = margin
    else:  # RIGHT
        x = max(margin, frame_w - text_width - margin)

    y = max(text_height + margin, margin + text_height)

    # Background rectangle for readability
    top_left = (max(0, x - padding), max(0, y - text_height - padding))
    bottom_right = (
        min(frame_w - 1, x + text_width + padding),
        min(frame_h - 1, y + baseline + padding),
    )

    cv2.rectangle(
        frame,
        top_left,
        bottom_right,
        color=(0, 0, 0),
        thickness=-1,
        lineType=cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        text,
        org=(x, y),
        fontFace=font,
        fontScale=font_scale,
        color=(255, 255, 255),
        thickness=thickness,
        lineType=cv2.LINE_AA,
    )

    return frame


def add_text_left_of_point(
    frame : np.ndarray,
    lines : list[str],
    center_left: Point,
    left_offset: int = 0,
    font=cv2.FONT_HERSHEY_SIMPLEX,
    font_scale: float = 0.7,
    color=(255, 255, 255),
    thickness: int = 2,
    line_spacing: int = 10,
    is_in_inches: bool = False,
):
    """
    Draw `lines` vertically centered around center_left.y, with all lines
    left-aligned at center_left.x + left_offset.

    `center_left` is a Point-like object with .x and .y attributes.
    """
    if not lines:
        return frame

    # if the given point is in field inches convert to screen pixels
    if is_in_inches:
        center_left = inches_to_screen(center_left)

    # Measure each line
    text_sizes = []
    for text in lines:
        (w, h), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )
        text_sizes.append((w, h, baseline))

    line_heights = [h + baseline for _, h, baseline in text_sizes]
    total_height = sum(line_heights) + line_spacing * (len(lines) - 1)

    # Start at the top of the text block
    y = center_left.y - total_height // 2
    x = center_left.x + left_offset

    for text, (_, h, baseline) in zip(lines, text_sizes):
        # putText's origin is the bottom-left of the text
        cv2.putText(
            img=frame,
            text=text,
            org=(int(x), int(y) + h),
            fontFace=font,
            fontScale=font_scale,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )
        y += h + baseline + line_spacing

    return frame


def draw_object_to_frame(
    frame: np.ndarray,
    object_dict: dict,
    color: tuple[int, int, int] = (0, 0, 0),
    thickness: int = 5,
) -> np.ndarray:
    """
    Draw an object onto a BGR frame as either a circle or square.

    Expected object_dict keys:
        - width: diameter for a circle, side length for a square
        - area: object area in pixels
        - center_x: horizontal center position
        - center_y: vertical center position
        - shape: "circle" or "square"

    Returns:
        np.ndarray: The frame with the object drawn.
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(
            f"frame must be numpy.ndarray, got {type(frame).__name__}"
        )

    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(
            f"frame must be a 3-channel BGR image, got shape {frame.shape}"
        )

    if not isinstance(object_dict, dict):
        raise TypeError(
            f"object_dict must be dict, got {type(object_dict).__name__}"
        )

    required_keys = {"WIDTH_PX", "AREA_PX", "CENTER_X_PX", "CENTER_Y_PX", "SHAPE", OBJECT_NAME}
    missing_keys = required_keys - object_dict.keys()
    if missing_keys:
        raise KeyError(
            f"object_dict is missing required keys: {sorted(missing_keys)}"
        )

    shape = str(object_dict["SHAPE"]).lower()
    if shape not in ("circle", "square", "no_shape"):
        raise ValueError(
            f"shape must be 'circle' or 'square', got {object_dict['SHAPE']!r}"
        )

    center_x = object_dict["CENTER_X_PX"]
    center_y = object_dict["CENTER_Y_PX"]
    width = object_dict["WIDTH_PX"]

    for name, value in (
        ("CENTER_X_PX", center_x),
        ("CENTER_Y_PX", center_y),
        ("WIDTH_PX", width),
    ):
        if not isinstance(value, (int, float, np.integer, np.floating)):
            raise TypeError(f"{name} must be a number, got {type(value).__name__}")

    if width <= 0:
        return frame

    center = (int(round(center_x)), int(round(center_y)))

    if shape == "circle":
        radius = int(round(width / 2))
        cv2.circle(
            img=frame,
            center=center,
            radius=radius,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )
    elif shape == "square":
        half_side = width / 2
        top_left = (
            int(round(center_x - half_side)),
            int(round(center_y - half_side)),
        )
        bottom_right = (
            int(round(center_x + half_side)),
            int(round(center_y + half_side)),
        )

        cv2.rectangle(
            img=frame,
            pt1=top_left,
            pt2=bottom_right,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )

    elif shape == "no_shape":
        pass


    return frame


def draw_circle_to_frame(frame: np.ndarray, center: Point, radius: int, color: tuple[int,int,int]=WHITE) -> np.ndarray:

    centerpoint = (int(center.x), int(center.y))

    frame = cv2.circle(
        img= frame,
        radius= radius,
        center= centerpoint,
        color= color,
        thickness= PIXELS_PER_INCH
    )

    return frame


def draw_detection_to_camera_frame(camera_frame: np.ndarray, detection: Detection, draw_arrow: bool = True) -> np.ndarray:
    '''draw a circle around the detection in the camera frame if possible'''

    

    if detection.in_frame == False:
        return camera_frame

    draw_color = color_dict[detection.name]
    camera_frame = draw_circle_to_frame(camera_frame, detection.camera_pos_px, radius= int(detection.width_px/2), color=draw_color)

    detect_lines = get_detection_lines(detection)

    if draw_arrow:
        camera_frame = draw_arrow_point_to_point(frame=camera_frame, start= CAMERA_CENTER_BOTTOM, end= detection.camera_pos_px, color=draw_color)

    
    camera_frame = add_text_left_of_point(camera_frame, center_left= detection.camera_pos_px, lines=detect_lines, left_offset= int((detection.width_px/2)*1.2) )


    return camera_frame


def draw_detection_list_to_camera_frame(camera_frame: np.ndarray, detect_list : list[Detection]) -> np.ndarray:

    for detection in detect_list:
        detection : Detection

        camera_frame = draw_detection_to_camera_frame(camera_frame, detection)

    return camera_frame


def draw_detection_to_field(
        field_frame: np.ndarray, 
        detection: Detection, 
        robot_pos: Point = FIELD_GOALBOX_CENTER_BOTTOM, 
        robot_bearing: float = BEARING_NORTH,
        draw_arrow: bool = False,
        draw_lines : bool = False) -> np.ndarray:
    if detection.in_frame == False:
        return field_frame

    detection_pos_in : Point = convert_to_field(
        object_bearing_rad= detection.ang_from_bot_rad,
        object_dis= detection.dis_from_bot_in,
        robot_bearing_rad= robot_bearing,
        robot_pos= robot_pos
    )

    if detection.name == BALL_RED:
        field_frame = draw_ball_to_field(
            field_frame= field_frame,
            ball_pos_in= detection_pos_in
        )

    elif (detection.name == HAT_BLUE) or (detection.name == HAT_YELLOW):
        field_frame = draw_robot_to_field(
            field_frame=field_frame,
            pos_in= detection_pos_in
        )


    if draw_arrow:
        detection_draw_color = get_draw_color(detection)
        field_frame = draw_arrow_point_to_point(field_frame, robot_pos, detection_pos_in, is_in_inches= True, color=detection_draw_color)

    if draw_lines:
        detect_lines = get_detection_lines(detection)
        field_frame = add_text_left_of_point(field_frame, detect_lines, detection_pos_in, is_in_inches=True, color= WHITE)

    return field_frame


def get_draw_color(detection : Detection) -> tuple[int,int,int]:
    '''search the detection name and return the color it should be drawn'''

    if detection.name == BALL_RED:
        return RED
    elif detection.name == HAT_BLUE:
        return BLUE
    elif detection.name == HAT_FUCHSIA:
        return FUCHSIA
    elif detection.name == HAT_YELLOW:
        return YELLOW
    elif detection.name == HAT_GREEN:
        return GREEN
    else:
        return WHITE


def clamp_to_field(given_point_in: Point, label: str = "") -> Point:
    '''ensure that the point is on the field'''

    if given_point_in.x < 0:
        #print(f"{label} clamped left")
        given_point_in.x = 0

    if given_point_in.x > playing_field_in_x:
        #print(f"{label} clamped right")
        given_point_in.x = playing_field_in_x

    if given_point_in.y < 0:
        #print(f"{label} clamped bottom")
        given_point_in.y = 0

    if given_point_in.y > playing_field_in_y:
        #print(f"{label} clamped top")
        given_point_in.y = playing_field_in_y

    return given_point_in


def draw_vertical_line_on_camera_frame(frame: np.ndarray, dis_from_left: int = 0, label = "") -> np.ndarray:
    '''draw a vertical line on the camera frame at a specified distance in pixels from the left'''

    point_top = Point(dis_from_left, 0)
    point_bottom = Point(dis_from_left, CAMERA_CAPTURE_Y)
    point_middle = Point(dis_from_left, SCREEN_CENTER_Y)

    if label != "":
        frame = add_text_left_of_point(frame, [label], center_left= point_middle)

    frame = draw_line_point_to_point(frame, point_top, point_bottom, color= WHITE)



    return frame


def draw_angle_lines_on_camera_frame(
        frame: np.ndarray, 
        add_text: bool = False,
        list_of_angles_deg: list[float] = [-30.0, -20.0, -10.0, 0.0, 10.0, 20.0, 30.0]) -> np.ndarray:
    '''draw vertical lines for each deg listed and return the frame'''

    

    adjacent_side = SCREEN_CENTER_X / math.tan(math.radians(31.1))

    for angle_deg in list_of_angles_deg:
        opposite_side = adjacent_side * math.tan(math.radians(angle_deg))
        opposite_side_px = int(opposite_side)

        dis_from_left = SCREEN_CENTER_X + opposite_side_px
        # print("dis from left px: ", dis_from_left)

        if add_text == False:
            label = ""
        else:
            label =  f"{angle_deg}deg"

        frame = draw_vertical_line_on_camera_frame(frame, dis_from_left, label=label)

    return frame


def draw_fieldstate(field_frame: np.ndarray, fieldstate: FieldState, draw_arrows: bool = True) -> np.ndarray:

    # draw our bot
    field_frame = draw_robot_to_field(
        field_frame= field_frame,
        bearing_rad= fieldstate.our_bot_bearing_rad,
        pos_in= clamp_to_field(fieldstate.our_bot_pos_in, "bot_us"),
        color= fieldstate.our_team_color
    )

    # draw the ball
    if fieldstate.ball_is_seen:

        if fieldstate.ball_is_ours:
            outline_color = fieldstate.our_team_color
        elif fieldstate.ball_is_theirs:
            outline_color = fieldstate.their_team_color
        else:
            outline_color = BLACK

        field_frame = draw_ball_to_field(
            field_frame= field_frame,
            ball_pos_in= clamp_to_field(fieldstate.ball_pos_in, "ball"),
            outline_color= outline_color
        )

        if draw_arrows:
            field_frame = draw_arrow_point_to_point(
                frame=field_frame,
                start= inches_to_screen(fieldstate.our_bot_pos_in),
                end= inches_to_screen(fieldstate.ball_pos_in),
                color= RED,
            )

    # draw the opponent
    if fieldstate.their_bot_is_seen:
        field_frame = draw_robot_to_field(
            field_frame= field_frame,
            bearing_rad= fieldstate.their_bot_bearing_rad,
            pos_in= clamp_to_field(fieldstate.their_bot_pos_in, "bot_them"),
            color= fieldstate.their_team_color
        )

        if draw_arrows:
            field_frame = draw_arrow_point_to_point(
                frame=field_frame,
                start= inches_to_screen(fieldstate.our_bot_pos_in),
                end= inches_to_screen(fieldstate.their_bot_pos_in),
                color= fieldstate.their_team_color
            )


    
    return field_frame



def draw_detection_left_right_to_frame_left(
        frame_camera_left: np.ndarray, 
        detection_left: Detection, 
        detection_right: Detection,
        draw_arrows: bool = False) -> np.ndarray:
    '''
    Draw circles around detections and arrows to the detections on the camera frame. Using the left frame, draw arrows from the bottom left third and right third,
    simulating two eyes without needing to show both camera frames
    '''

    point_bottom_left_third = Point(int(CAMERA_CAPTURE_X / 3), CAMERA_CAPTURE_Y)
    point_bottom_right_third = Point(int(CAMERA_CAPTURE_X * 2 /3), CAMERA_CAPTURE_Y)

    draw_color = get_draw_color(detection_left)

    # if the right cam sees what the left doesn't draw an arrow to the middle right to show it's over there
    point_middle_right = Point(CAMERA_CAPTURE_X, SCREEN_CENTER_Y)

    # if neither see it, return the unchanged frame
    if (detection_left.in_frame == False) and (detection_right.in_frame == False):
        return frame_camera_left

    # if only the left sees it, draw the arrow from bottom left third to detection
    elif (detection_left.in_frame == True) and (detection_right.in_frame == False):
        frame_camera_left = draw_detection_to_camera_frame(frame_camera_left, detection_left, draw_arrow= False)
        
        if draw_arrows:
            frame_camera_left = draw_arrow_point_to_point(frame_camera_left, start= point_bottom_left_third, end= detection_left.camera_pos_px, color= draw_color)

    # if only the right sees it, draw the arrow from bottom right third to off screen
    elif (detection_left.in_frame == False) and (detection_right.in_frame == True):
        
        if draw_arrows:
            frame_camera_left = draw_arrow_point_to_point(frame_camera_left, start= point_bottom_right_third, end= point_middle_right, color= draw_color)

    # if both see it, draw an arrow from both bottom thirds
    else:
        frame_camera_left = draw_detection_to_camera_frame(frame_camera_left, detection_left, draw_arrow= False)
        
        if draw_arrows:
            frame_camera_left = draw_arrow_point_to_point(frame_camera_left, start= point_bottom_left_third, end= detection_left.camera_pos_px, color= draw_color)
            frame_camera_left = draw_arrow_point_to_point(frame_camera_left, start= point_bottom_right_third, end= detection_left.camera_pos_px, color= draw_color)

    return frame_camera_left


def draw_two_cams_to_one(
        frame_camera_left: np.ndarray, 
        list_detections_left: list[Detection], 
        list_detections_right: list[Detection],
        draw_arrows: bool = False) -> np.ndarray:
    '''
    Draw circles around detections and arrows to the detections on the camera frame. Using the left frame, draw arrows from the bottom left third and right third,
    simulating two eyes without needing to show both camera frames
    '''

    for detect_left, detect_right in zip(list_detections_left, list_detections_right):
        frame_camera_left = draw_detection_left_right_to_frame_left(frame_camera_left, detect_left, detect_right, draw_arrows)


    return frame_camera_left


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


def get_lcd_lines(fieldstate : FieldState) -> list[str]:
    ball_pos = "???"

    # or X,Y so either way 3 char
    if fieldstate.ball_is_seen:
        ball_pos = f"{round(fieldstate.ball_pos_in.x)},{round(fieldstate.ball_pos_in.y)}"

    their_bot_pos ="???"
    if fieldstate.their_bot_is_seen:
        their_bot_pos = f"{round(fieldstate.their_bot_pos_in.x)},{round(fieldstate.their_bot_pos_in.y)}"

    our_bot_pos = f"{round(fieldstate.our_bot_pos_in.x)},{round(fieldstate.our_bot_pos_in.y)}"        # (0.0,0.0)
    our_bot_command = fieldstate.com_str + str(round(fieldstate.com_dur_sec,1))     # something like W1.1

    row1 = fieldstate.status_str
    row2 = f"us {our_bot_pos} op {their_bot_pos}"
    row3 = f"ball {ball_pos}"
    row4 = f"com {our_bot_command}"

    return [row1, row2, row3, row4]


def get_lcd_frame_fieldstate(fieldstate: FieldState) -> np.ndarray:
    '''get the lcd frame with text from a given fieldstate'''
    list_lines = get_lcd_lines(fieldstate)

    lcd_frame = get_lcd_frame(list_lines= list_lines)
    return lcd_frame
