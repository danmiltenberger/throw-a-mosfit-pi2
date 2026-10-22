import cv2
import numpy as np
from constants import *
from variables import *
from classes import Rectangle, Point, get_point_int_tuple, FieldState
from tam_library import load_image_as_frame
from annotate_frames import draw_outlined_circle
import math


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


def get_field_frame() -> np.ndarray:

    if USE_DRAWN_FIELD:
        frame = load_image_as_frame("field_empty.png")
    else:
        frame = load_image_as_frame("field_black.png")

    return frame


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


def draw_notched_rectangle(
    image : np.ndarray,
    center_x : int,
    top_y : int,
    width : int,
    height : int,
    base_length : int,
    angle_deg : int,
    color=(255, 255, 255),
    rotation_deg=0.0,
    border_thickness=1,
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

    notch_depth = (base_length / 2) / np.tan(
        np.deg2rad(angle_deg / 2)
    )
    if notch_depth >= height:
        raise ValueError("The notch must be shallower than the rectangle.")

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

    cv2.fillPoly(
        image,
        [points],
        color=color,
        lineType=cv2.LINE_AA,
        shift=shift,
    )

    black = 0 if image.ndim == 2 else (0,) * image.shape[2]

    cv2.polylines(
        image,
        [points],
        isClosed=True,
        color=black,
        thickness=int(border_thickness),
        lineType=cv2.LINE_AA,
        shift=shift,
    )

    return image


def draw_field_from_field_state(
    field_frame: np.ndarray, state: FieldState
) -> np.ndarray:

    if draw_ball_red:
        ball_pos_px = inches_to_screen(state.ball_pos_in)

        field_frame = draw_outlined_circle(
            image=field_frame,
            center_x=int(ball_pos_px.x),
            center_y=int(ball_pos_px.y),
            color=RED,
            radius=convert_to_px(BALL_RED_RADIUS_IN),
        )

    # FIXME
    OUR_TEAM_COLOR = YELLOW

    if draw_our_bot:

        our_bot_pos_px = inches_to_screen(state.our_bot_pos_in)

        field_frame = draw_notched_rectangle(
            image=field_frame,
            center_x=int(our_bot_pos_px.x),
            top_y=int(our_bot_pos_px.y - convert_to_px(BOT_RADIUS_IN)),
            width=convert_to_px(BOT_RADIUS_IN) * 2,
            height=convert_to_px(BOT_RADIUS_IN) * 2,
            base_length=convert_to_px(BALL_RED_RADIUS_IN) * 2,
            angle_deg=90,
            color=OUR_TEAM_COLOR,
            rotation_deg=math.degrees(state.our_bot_bearing_rad),
            border_thickness=1,
        )

    THEIR_TEAM_COLOR = BLUE
    if draw_their_bot:
        their_bot_pos_x = inches_to_screen(state.their_bot_pos_in)

        field_frame = draw_notched_rectangle(
            image=field_frame,
            center_x=int(their_bot_pos_x.x),
            top_y=int(their_bot_pos_x.y - convert_to_px(BOT_RADIUS_IN)),
            width=convert_to_px(BOT_RADIUS_IN) * 2,
            height=convert_to_px(BOT_RADIUS_IN) * 2,
            base_length=convert_to_px(BALL_RED_RADIUS_IN) * 2,
            angle_deg=90,
            color=THEIR_TEAM_COLOR,
            rotation_deg=math.degrees(state.their_bot_bearing_rad),
            border_thickness=1,
        )

    return field_frame





if __name__ == "__main__":
    draw_empty_field(is_show_image=True, draw_centerpoints=False, save_image=True)
    draw_empty_field(just_black=True)