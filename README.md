Now that we've spent hours on the first one, we know what to do!

throw-a-mosfit-pi2 is our Mechatronics Fall 2026 project to WIN a soccer match. 
This repository contains all of the code that will be running on our raspberry pi (was 4, but we upgraded to a 5 for dual cameras)

### Code Process
#### Getting the Fieldstate
1. Get the left and right image from the cameras
    tam_binocular handles setting up cameras and getting frames
2. Detect objects in the frame by sorting by color (goalpost are green and purple, ball is red, opponent is either yellow or blue)
    tam_hsv handles loading the dictionary of values and allows tuning
3. These detected objects are saved in a class called a CameraState, one for each camera
    We can also pull BotCommands from a CameraState just in case our cool top down algorithm doesn't behave as we hope
4. CameraStates are combined togther to create a FieldState
    Angle of the object is found by comparing the center position in the frame with the camera's 62.2deg horizontal field of view and total frame pixels
    Range of the object is found either:
        With both angles of the cameras and using angle-side-angle triangulation OR
        If one camera sees it, comparing the perceieved width in pixels to a known width and interpreting the distance
    Since the goalposts don't move, we update the ROBOT's position with these fixed positions
        The four possible angles are:
            LE - left eye to east
            LW - left eye to west
            RE - right eye to east
            RW - right eye to west
        The lines we know are
            WE - distance between goalposts (48in)
5. FieldStates are blended together with previous states to try and remove random noise in our measurements
6. Send the blended FS to the decisionmaking portion of the code
    The advantage of this approach is we can test all sorts of different fieldstates without having to actually record the images. Vision and decision are decoupled

#### Getting commands
        
        
        


### IP info
IP at home: 10.0.0.50
IP at school: 10.201.20.28
pi5 ip at school: 10.201.6.89


### rpi cam commands
rpicam-hello --list-cameras
rpicam-hello --timeout 0


### autostart commands
# rpi has a setup to automatically display the IP and time to the LCD, but it can compete with lcd display during the game
sudo systemctl stop switches.service      # stop it now
sudo systemctl disable switches.service   # don't start at boot
sudo systemctl restart switches.service   # after editing your script


### Goals
center to center horizontal = 48in
center to center vertical = 23in
