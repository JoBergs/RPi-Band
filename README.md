# RPi-Band

RPi-Band fuses the Pimoroni Piano HAT and Drum HAT code to a single software,
which gives the possibility for playing two intruments on a single Raspberry Pi.
The code in this repository is Python3, but rewriting for Python2 should be no issue.

# Tutorial
Find more info in my tutorial  
http://www.knight-of-pi.org/rpi-band-drumhat-and-pianohat-simultaneously-on-a-single-raspberry-pi/

# Hardware setup
![Alt text](rpi_band_setup.jpg?raw=true "RPi-Band")

# Installing RPi-Band

    cd ~
    sudo apt-get install python3-pianohat
    sudo apt-get install python3-drumhat
    git clone https://github.com/JoBergs/RPi-Band


# Usage

    cd ~/RPi-band
    python3 rpi-band.py

# Autostart
Opening .bashrc with

    sudo nano ~/.bashrc
and add the line

    python3 /home/pi/RPi-Band/rpi-band.py

# Parent GitHub repositories and original READMEs 
Piano HAT: https://github.com/pimoroni/Piano-HAT  
Drum HAT: https://github.com/pimoroni/Drum-HAT