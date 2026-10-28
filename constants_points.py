from classes import Point, Line


### Defining the field, everything in inches
FIELD_CENTER = Point(48,72)

GOALPOST_SOUTHWEST = Point(24,0)
GOALPOST_SOUTHEAST = Point(72,0)
GOALPOST_NORTHWEST = Point(24,144)
GOALPOST_NORTHEAST = Point(72,144)

FIELD_SOUTHWEST_CORNER = Point(0,0)
FIELD_SOUTHEAST_CORNER = Point(96,0)
FIELD_NORTHWEST_CORNER = Point(0,144)
FIELD_NORTHEAST_CORNER = Point(96,144)

FIELD_GOALBOX_CENTER_BOTTOM = Point(48,12)
FIELD_GOALBOX_CENTER_TOP = Point(48,132)
FIELD_GOAL_CENTER_TOP = Point(48,144)
FIELD_GOAL_CENTER_BOTTOM = Point(48,0)

# octogon points
# top
OCTOGON_1 = Point(12,144)
OCTOGON_2 = Point(84, 144)

# right
OCTOGON_3 = Point(96, 132)
OCTOGON_4 = Point(96, 12)

# bottom
OCTOGON_5 = Point(84, 0)
OCTOGON_6 = Point(12,0)

# left
OCTOGON_7 = Point(0,12)
OCTOGON_8 = Point(0, 132)

# define the lines that make up the octagon
line_goal_top = Line(
    pt1= GOALPOST_NORTHWEST,
    pt2= GOALPOST_NORTHEAST
)

line_topright_horizontal = Line(
    pt1= GOALPOST_NORTHEAST,
    pt2= OCTOGON_2,
)

line_topright_diag = Line(
    pt1= OCTOGON_2,
    pt2= OCTOGON_3
)

line_right_vert = Line(
    pt1= OCTOGON_3,
    pt2= OCTOGON_4
)

line_botright_diag = Line(
    pt1= OCTOGON_4,
    pt2= OCTOGON_5
)

line_botright_horiontal = Line(
    pt1= OCTOGON_5,
    pt2= GOALPOST_SOUTHEAST
)

line_goal_bot = Line(
    pt1= GOALPOST_SOUTHEAST,
    pt2= GOALPOST_SOUTHWEST,
)

line_botleft_horizontal = Line(
    pt1= GOALPOST_SOUTHWEST,
    pt2= OCTOGON_6
)

line_botleft_diag = Line(
    pt1= OCTOGON_6,
    pt2= OCTOGON_7
)

line_left_vert = Line(
    pt1= OCTOGON_7,
    pt2= OCTOGON_8
)

line_topleft_horizontal = Line(
    pt1= OCTOGON_8,
    pt2= GOALPOST_NORTHWEST
)


perim_octogon : list = [
    OCTOGON_1, OCTOGON_2, OCTOGON_3, OCTOGON_4, OCTOGON_5, OCTOGON_6, OCTOGON_7, OCTOGON_8
]