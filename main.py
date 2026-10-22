import time
from constants import *
from variables import *
from pathlib import Path

from penalty_kick import penalty_kick
from system_check import system_check
from play_match import play_match
from tam_library import check_button, tamprint

match_settings = MatchSettings()


def main():
    """the program that runs it all!"""

    tamprint("beginning program")
    setup_folders()

    tamprint("loading default match settings")

    if RUN_SYSTEM_CHECK:
        tamprint("beginning system check")
        system_check()

    # always wait for a specific button
    WAITING_FOR_START = True

    while True:

        # look for buttons that can START the game
        if WAITING_FOR_START:

            # read values of buttons and do their special subroutines
            if check_button(CHANGE_TEAM):
                change_team()

            if check_button(PENALTY_KICK):
                penalty_kick()

            # or do the most special subroutine of all, the game!
            if check_button(START_GAME):
                WAITING_FOR_START = False

        else:
            play_match()  # breaks if button(NEW_MATCH)
            WAITING_FOR_START = True








def setup_folders():
    """Create necessary directories that might be gitignored"""

    tamprint("ensuring all necessary folders are created")
    for folder in folder_list:
        Path(folder).mkdir(parents=True, exist_ok=True)


def change_team():
    """update the field view and robot colors"""

    if match_settings.OUR_TEAM_COLOR == YELLOW_TEAM:

        match_settings.OUR_TEAM_COLOR = BLUE_TEAM
        match_settings.THEIR_TEAM_COLOR = YELLOW_TEAM

    elif match_settings.OUR_TEAM_COLOR == BLUE_TEAM:
        match_settings.OUR_TEAM_COLOR = YELLOW_TEAM
        match_settings.THEIR_TEAM_COLOR = BLUE_TEAM

    else:
        tamprint(
            f"Unexpected team color, got {match_settings.OUR_TEAM_COLOR}, expected 'YELLOW' or 'BLUE'"
        )

    # TODO - change field view, etc
    pass


if __name__ == "__main__":
    main()
