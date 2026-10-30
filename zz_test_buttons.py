import time
import RPi.GPIO as GPIO # pyright: ignore[reportMissingModuleSource]
from I2C_write import write_lcd_lines

START_MATCH = 5
START_KICK = 6
CHANGE_TEAM = 13
CHANGE_GOAL = 19
END = 26

BUTTONS = [START_MATCH, START_KICK, CHANGE_TEAM, CHANGE_GOAL, END]

# Menu / game state
state = {
    "mode": "MENU",          # MENU, MATCH, PENALTY_KICK
    "team_color": "YELLOW",  # YELLOW or BLUE
    "goal_color": "PURPLE",  # PURPLE or GREEN
    "start_time": None,
}

def write_state_to_lcd(state : dict):
    list = [
        f"mode: {state["mode"]}",
        f"team_color: {state["team_clor"]}",
        f"goal_color: {state["goal_color"]}",
        f"start_time: {state["start_time"]}",
    ]

    write_lcd_lines(list)





def run_match():
    """Placeholder for a normal match."""
    elapsed = time.monotonic() - state["start_time"]
    print(f"[MATCH] Elapsed time: {elapsed:.1f} seconds")


def run_penalty_kick():
    """Placeholder for a penalty kick."""
    elapsed = time.monotonic() - state["start_time"]
    print(f"[PENALTY KICK] Elapsed time: {elapsed:.1f} seconds")


def return_to_menu():
    state["mode"] = "MENU"
    state["start_time"] = None
    print("[MENU] Returned to menu")


def handle_button(pin):
    mode = state["mode"]

    # END works from any active game mode
    if pin == END:
        if mode in ("MATCH", "PENALTY_KICK"):
            return_to_menu()
            write_state_to_lcd(state)
        return

    if mode == "MENU":
        if pin == CHANGE_TEAM:
            state["team_color"] = (
                "BLUE" if state["team_color"] == "YELLOW" else "YELLOW"
            )
            print(f"[MENU] Team color: {state['team_color']}")
            write_state_to_lcd(state)

        elif pin == CHANGE_GOAL:
            state["goal_color"] = (
                "GREEN" if state["goal_color"] == "PURPLE" else "PURPLE"
            )
            print(f"[MENU] Goal color: {state['goal_color']}")
            write_state_to_lcd(state)

        elif pin == START_MATCH:
            state["mode"] = "MATCH"
            state["start_time"] = time.monotonic()
            write_state_to_lcd(state)
            run_match()

        elif pin == START_KICK:
            state["mode"] = "PENALTY_KICK"
            state["start_time"] = time.monotonic()
            write_state_to_lcd(state)
            run_penalty_kick()

    elif mode == "MATCH":
        if pin == START_MATCH:
            run_match()
            write_state_to_lcd(state)

    elif mode == "PENALTY_KICK":
        if pin == START_KICK:
            run_penalty_kick()
            write_state_to_lcd(state)


def button_callback(pin):
    handle_button(pin)


def setup_buttons():
    GPIO.setmode(GPIO.BCM)

    for pin in BUTTONS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            pin,
            GPIO.FALLING,
            callback=button_callback,
            bouncetime=150,
        )


def cleanup():
    GPIO.cleanup()


if __name__ == "__main__":
    try:
        setup_buttons()
        print("Ready. Press buttons...")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()