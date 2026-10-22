from dataclasses import dataclass

# Button Constants
CHANGE_TEAM = "CHANGE_TEAM"
NEW_MATCH = "NEW_MATCH"
PENALTY_KICK = "PENALTY_KICK"
START_GAME = "START_GAME"

# Folder Constants
TRAINING_DATA = "training_data"
FIELD_STATES = "field_states"

# Color Constants
YELLOW = "YELLOW"
BLUE = "BLUE"
FUCHSIA = "FUCHSIA"
GREEN = "GREEN"


folder_list = [TRAINING_DATA, FIELD_STATES]

@dataclass 
class MatchSettings:

    # Game states
    WAITING_FOR_START: bool = True

    # Game vars
    OUR_TEAM_COLOR: str = YELLOW
    THEIR_TEAM_COLOR: str = BLUE
    GOAL_EAST_COLOR: str = FUCHSIA
    GOAL_WEST_COLOR: str = GREEN


