

## Switch labels
# team_color
# goal_color
# match_type
# recording

switch_pin_team_color = 26
switch_pin_goal_color = 19
switch_pin_match_type = 13
switch_pin_recording = 6


import RPi.GPIO as GPIO          #Import GPIO library
import time                      #Import time library

GPIO.setmode(GPIO.BCM)

GPIO.setup(switch_pin_team_color, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Enable input and pull up resistors
GPIO.setup(switch_pin_goal_color, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Enable input and pull up resistors
GPIO.setup(switch_pin_match_type, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Enable input and pull up resistors
GPIO.setup(switch_pin_recording, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Enable input and pull up resistors


while True:

    switch_team_color_on = GPIO.input(switch_pin_team_color)
    switch_goal_color_on = GPIO.input(switch_pin_goal_color)
    switch_match_type_on = GPIO.input(switch_pin_match_type)
    switch_recording_on = GPIO.input(switch_pin_recording)

    status_str = f"team: {switch_team_color_on} goal: {switch_goal_color_on} match:{switch_match_type_on} rec:{switch_recording_on}"


    print(status_str)