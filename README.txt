Now that we've spent hours on the first one, we know what to do!


IP at home: 10.0.0.50
IP at school: 10.201.20.28


pi5 ip at school: 10.201.6.89


### rpi cam commands
rpicam-hello --list-cameras
rpicam-hello --timeout 0


### autostart commands
# rpi has a setup to automatically display the IP and time to the LCD, but it can compete with lcd display
sudo systemctl stop switches.service      # stop it now
sudo systemctl disable switches.service   # don't start at boot
sudo systemctl restart switches.service   # after editing your script