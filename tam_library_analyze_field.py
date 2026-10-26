'''collection of fxns to determine if items are within zones, etc'''


from classes import Point, Line


def is_on_line(point_in_q: Point, line: Line) -> bool:
    # check if a given point lies on the line between points

    # equation of line: y = mx + b
    rise = line.pt2.y - line.pt1.y
    run = line.pt2.x - line.pt1.x
    m = rise / run

    # solve for b (y intercept) using one of the poitns
    b = line.pt1.y - m * line.pt1.x

    # check if new point lies along the line
    calc_y = m * point_in_q.x + b

    # round to nearest whole num
    calc_y = round(calc_y)
    given_y = round(point_in_q.y)

    if calc_y == given_y:
        return True
    else:
        return False


def is_within_rect(point_in_q: Point, top_left: Point, bot_right: Point) -> bool:
    # check x

    within_x: bool = False
    within_y: bool = False

    if top_left.x <= point_in_q.x <= bot_right.x:
        within_x = True

    if bot_right.y <= point_in_q.y <= top_left.y:
        within_y = True

    if within_x and within_y:
        return True
    else:
        return False


def is_within_circ(point_in_q: Point, circle_center: Point, cicle_rad: float) -> bool:
    """Return True if the point is inside or on the circle."""
    if cicle_rad < 0:
        raise ValueError("Circle radius must be non-negative.")

    dx = point_in_q.x - circle_center.x
    dy = point_in_q.y - circle_center.y

    return dx * dx + dy * dy <= cicle_rad * cicle_rad

