#!/usr/bin/env python3

import argparse
import glob
import math
import os
import pygame
import re
import signal
import subprocess
import sys
import time

import drumhat
import pianohat
import RPi.GPIO as GPIO

DESCRIPTION = '''This script integrates Pimoronis Piano HAT and Drum HAT software and gives you simple, ready-to-play instruments which use .wav files located in sounds.
The parameter -p expects the name of the directory containing the sounds that should be loaded onto the piano HAT first
and -d expects the name of the directory containing the sounds that should be loaded onto the drum HAT.
For the 8-Bit-synthesizer, pass "8bit" for -p.


Press CTRL+C to exit.'''

# accept 8bit for the synthi, extend sound_sets by it but handle specially 
SOUND_BASEDIR = os.path.join(os.path.dirname(__file__), "sounds/")

# list of all available soundsets
sound_sets = [os.path.basename(tmp) for tmp in glob.glob(os.path.join(SOUND_BASEDIR, "*"))]

sound_sets.append("8bit")

GPIO.setmode(GPIO.BCM)

# safe shutdown button is pin 14 (GND) and pin 18(IO: 24 in BCM) in BOARD numbering
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

############## synthi constants
SAMPLERATE = 44100
BITRATE = 8

ATTACK_MS = 25
RELEASE_MS = 500

# Feel free to change the volume!
volume = {'sine':0.8, 'saw':0.4, 'square':0.4}

wavetypes = ['sine','saw','square']
enabled = {'sine':True, 'saw':False, 'square':False}
notes = {'sine':[],'saw':[],'square':[]}


# The samples are 8bit signed, from -127 to +127
# so the max amplitude of a sample is 127
max_sample = 2**(BITRATE - 1) - 1

def wave_sine(freq, time):
    """Generates a single sine wave sample"""
    s = math.sin(2*math.pi*freq*time)
    return int(round(max_sample * s ))


def wave_square(freq, time):
    """Generates a single square wave sample"""
    return -max_sample if freq*time < 0.5 else max_sample


def wave_saw(freq, time):
    """Generates a single sav wave sample"""
    s = ((freq*time)*2) - 1
    return int(round(max_sample * s)) 

# IMPORTANT
def generate_sample(frequency, volume=1.0, wavetype=None):
    """Generates a sample of a specific frequency and wavetype"""
    if wavetype is None:
        wavetype = wave_square

    sample_count = int(round(SAMPLERATE/frequency))

    buf = numpy.zeros((sample_count, 2), dtype = numpy.int8)

    for s in range(sample_count):
        t = float(s)/SAMPLERATE # Time index
        buf[s][0] = wavetype(frequency, t)
        buf[s][1] = buf[s][0] # Copy to stero channel

    sound = pygame.sndarray.make_sound(buf)
    sound.set_volume(volume) # Set the volume to balance sounds

    return sound

# generate samples
for f in [
        261.626,
        277.183,
        293.665,
        311.127,
        329.628,
        349.228,
        369.994,
        391.995,
        415.305,
        440.000,
        466.164,
        493.883,
        523.251
    ]:
    notes['sine'] += [generate_sample(f, volume=volume['sine'], wavetype=wave_sine)]
    notes['saw'] += [generate_sample(f, volume=volume['saw'], wavetype=wave_saw)]
    notes['square'] += [generate_sample(f, volume=volume['square'], wavetype=wave_square)]

############## /synthi constants


def parse_arguments(sysargs):
    """ Setup the command line options. """

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-p', '--piano', default='piano')
    parser.add_argument('-d', '--drums', default='drums2')

    return parser.parse_args(sysargs)


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]


MIXER_NORMAL = (44100, -16, 1, 512)
MIXER_8BIT = (44100, -8, 4, 256)

def set_mixer(mixer_values):

    pygame.mixer.quit()
    pygame.mixer.pre_init(*mixer_values)
    pygame.mixer.init()
    pygame.mixer.set_num_channels(32)

set_mixer(MIXER_NORMAL)


class Container:
    """ Container is a factory for creating instruments, necessary for 
    switching to 8-bit piano """

    piano = None
    drums = None

    def __init__(self, piano_index, drums_index):
        self.drums = Drums(drums_index)
        self.create_piano(piano_index)

        signal.pause()

    def create_piano(self, piano_index):
        if sound_sets[piano_index] == '8bit':
            # TESTING: set sounds to piano
            self.piano = Synthesizer(self, 1)
        else:
            self.piano = Piano(self, piano_index)


class Instrument:
    sounds = []
    sound_index = 0

    def __init__(self, sound_index):
        self.sound_index = sound_index
        self.load_sounds()

    def load_sounds(self):
        sounds_path = glob.glob(os.path.join(SOUND_BASEDIR, 
                                                   sound_sets[self.sound_index], "*.wav"))
        sounds_path.sort(key=natural_sort_key)
        self.sounds = [pygame.mixer.Sound(f) for f in sounds_path]  

class Drums(Instrument):

    def __init__(self, sound_index):
        super(Drums, self).__init__(sound_index)

        drumhat.on_hit(drumhat.PADS, self.handle_hit)
        drumhat.on_release(drumhat.PADS, self.handle_release)

    def handle_hit(self, event):
        # event.channel is a zero based channel index for each pad
        self.sounds[event.channel].play(loops=0)

    def handle_release(self):
        pass  


# maybe add a wrapper four outputting played sound  filename?
class Piano(Instrument):
    octave = 0
    octaves = 0 
    container = None
    mixer_settings = MIXER_NORMAL

    def __init__(self, container, sound_index):
        super(Piano, self).__init__(sound_index)

        self.container = container

        pianohat.on_note(self.handle_note)
        pianohat.on_octave_up(self.handle_octave_up)
        pianohat.on_octave_down(self.handle_octave_down)
        pianohat.on_instrument(self.handle_instrument)

        pianohat.auto_leds(True)

    def load_sounds(self):
        set_mixer(self.mixer_settings)  # reset mixer to normal mode

        super(Piano, self).load_sounds()

        self.octaves = len(self.sounds) / 12
        self.octave = int(self.octaves / 2)   

    # could be merged with handle_hit in Drum, but that'd be obfuscating
    def handle_note(self, channel, pressed):
        channel = channel + (12 * self.octave)

        if channel < len(self.sounds) and pressed:
            self.sounds[channel].play(loops=0)

    def handle_instrument(self, channel, pressed):
        if pressed:
            self.sound_index = (self.sound_index + 1) % len(sound_sets)
            self.container.create_piano(self.sound_index)

    def handle_octave_up(self, channel, pressed):
        if pressed and self.octave < int(self.octaves) - 1:
            self.octave += 1

    def handle_octave_down(self, channel, pressed):
        if pressed and self.octave > 0:
            self.octave -= 1

# SURPRESS sound generation?
# octave handling broken
# a different way for toggeling sine, square ect. is necessary: octave up/down needs to iterate over a list of all possible combinations
class Synthesizer(Piano):
    mixer_settings = MIXER_8BIT

    def __init__(self, container, sound_index):
        super(Synthesizer, self).__init__(container,  sound_index)   

    def handle_note(self, channel, pressed):
        """Handles the piano keys
        Any enabled samples are played, and *all* samples are turned off is a key is released
        """
        # OFF for testing
        #pianohat.set_led(channel, pressed)
        
        if pressed:
            for t in wavetypes:
                if enabled[t]:
                    notes[t][channel].play(loops=-1, fade_ms=ATTACK_MS)
        else:
            for t in wavetypes:
                notes[t][channel].fadeout(RELEASE_MS)


############## synthi code

# for first experiments, disable this (not necessary, we won't handle_instrument like below anyways)
def update_leds():
    """Updates the Instrument and Octave LEDs to show enabled samples"""
    pianohat.set_led(15, enabled['sine'])
    pianohat.set_led(14, enabled['saw'])
    pianohat.set_led(13, enabled['square'])

# IS IT NECESSARY TO HANDLE LED LIGHTING MANUALLY FOR MY CONCEPT???

# this will be handled differently; the first version should just stick with the default config
def handle_instrument(channel, pressed):
    """Handles the Instrument, Octave Up/Down keys
    These toggle Sine, Saw and Square waves on and off so you can combine them
    """
    if not pressed:
        return

    if channel == 15: # Sine
        enabled['sine'] = not enabled['sine']
        print("Sine: {}".format("ON" if enabled['sine'] else "OFF"))
    if channel == 14: # Saw
        enabled['saw'] = not enabled['saw']
        print("Saw: {}".format("ON" if enabled['saw'] else "OFF"))
    if channel == 13: # Square
        enabled['square'] = not enabled['square']
        print("Square: {}".format("ON" if enabled['square'] else "OFF"))

    update_leds()

# IMPORTANT
# called by on_note
def play_sample(channel, pressed):
    """Handles the piano keys
    Any enabled samples are played, and *all* samples are turned off is a key is released
    """
    pianohat.set_led(channel, pressed)
    if pressed:
        for t in wavetypes:
            if enabled[t]:
                notes[t][channel].play(loops=-1, fade_ms=ATTACK_MS)
    else:
        for t in wavetypes:
            notes[t][channel].fadeout(RELEASE_MS)


############## /synthi code


def turn_off(pin):
    """ Shutdown the Raspberry Pi; the argument pin is not required
    but passed by event_detect. """

    GPIO.cleanup()
    subprocess.call(['sudo poweroff'], shell=True)


if __name__ == "__main__":
    # optional shutdown button
    GPIO.add_event_detect(24, edge=GPIO.FALLING, callback=turn_off) 
    args = parse_arguments(sys.argv[1:]) 

    container = Container(sound_sets.index(args.piano), sound_sets.index(args.drums))
