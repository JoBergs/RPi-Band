# RPi-Band

RPi-Band fuses the Pimoroni Piano HAT and Drum HAT code to a single software,
which gives the possibility for playing two intruments on a single Raspberry Pi.


# ORIGINAL README Piano HAT

![Piano HAT](piano-hat-logo-new.png)

* 16 Capacitive Touch Buttons
* 13 Notes from C to C
* Octave Up/Down
* Instrument Select

Learn more: https://shop.pimoroni.com/products/piano-hat

# Installing Piano HAT

**Full install ( recommended ):**

We've created a super-easy installation script that will install all pre-requisites and get your Piano HAT up and running in a jiffy. To run it fire up Terminal which you'll find in Menu -> Accessories -> Terminal on your Raspberry Pi desktop like so:

![Finding the terminal](terminal.jpg)

In the new terminal window type the following and follow the instructions:

```bash
curl https://get.pimoroni.com/pianohat | bash
```

If you choose to download examples you'll find them in `/home/pi/Pimoroni/pianohat/`.

**Library install for Python 3:**

on Raspbian:

```bash
sudo apt-get install python3-pianohat
```
other environments: 

```bash
sudo pip3 install pianohat
```

**Library install for Python 2:**

on Raspbian:

```bash
sudo apt-get install python-pianohat
```
other environments: 

```bash
sudo pip2 install pianohat
```

In all cases you will have to enable the i2c bus.

# Documentation & Support

* Getting started - https://learn.pimoroni.com/tutorial/piano-hat/getting-started-with-piano-hat
* Function reference - http://docs.pimoroni.com/pianohat/
* GPIO Pinout - https://pinout.xyz/pinout/piano_hat
* Get help - http://forums.pimoroni.com/c/support

# Using Piano HAT

This library lets you use Piano HAT in Python to control whatever project you might assemble.

See `buttons.py` for an example of how to handle buttons. The library has 4 different events you can bind to:

* `on_note` - triggers when a piano key is touched
* `on_octave_up` - triggers when the Octave Up key is touched
* `on_octave_down` - triggers when the Octave Down key is touched
* `on_instrument` - triggeres when the Instrument key is touched

See `leds.py` for an example of how to take command of the Piano HAT LEDs. You can turn all of the LEDs on and off at will, useful for creating a visual metronome, prompting a user which key to press and more.

* `set_led(x, True/False)` - lets you set a particular LED to on ( True ) or off ( False ).
* `auto_leds(False)` - stops Piano HAT from automatically lighting the LEDs when a key is touched

# MIDI!

Piano HAT will also work with anything that supports MIDI input, thanks to Python MIDI and the `midi-piano.py` example.

## Installing Python MIDI

This is a little tricky, but if you follow these steps you should get it installed in no time:

First you'll need some dependencies, install them with: `sudo apt-get install python-dev libasound2-dev swig`

Next, you need to clone the GitHub repo: `git clone https://github.com/vishnubob/python-midi`

And install it: `cd python-midi && sudo ./setup.py install`

If it installs properly, you should get a handy new tool `mididumphw.py` which will tell you what MIDI-compatible synths you've got running and what Client/Port IDs you'll need to connect to to use them.

## Using `midi-piano.py`

You'll find the MIDI Piano example in the examples folder of this repository, or in `~/Pimoroni/piano-hat` if you used our installer script. By default it supports SunVox and yoshimi:

* Sunvox ( Get it from http://www.warmplace.ru/soft/sunvox/ )
* Yoshimi ( `sudo apt-get install yoshimi` )

Run either of these synths first, and then run `sudo ./midi-piano.py` and start playing. For best results, you should use a Pi 2- especially with Yoshimi which can be a bit taxing on the older models.

# ORIGINAL README Drum HAT
