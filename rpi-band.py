#!/usr/bin/env python3

import argparse
import glob
import os
import pygame
import re
import signal
import subprocess
import sys

import drumhat
import pianohat
import RPi.GPIO as GPIO

DESCRIPTION = '''This script integrates Pimoronis Piano HAT and Drum HAT software and gives you simple, 
ready-to-play instruments which use .wav files located in sounds.
The parameter -p expects the name of the directory containing the sounds that should be loaded onto the piano HAT first
and -d expects the name of the directory containing the sounds that should be loaded onto the drum HAT.

Press CTRL+C to exit.'''

# accept 8bit for the synthi, extend sound_sets by it but handle specially 
SOUND_BASEDIR = os.path.join(os.path.dirname(__file__), "sounds/")

# list of all available soundsets
sound_sets = [os.path.basename(tmp) for tmp in glob.glob(os.path.join(SOUND_BASEDIR, "*"))]

GPIO.setmode(GPIO.BCM)

# safe shutdown button is pin 14 (GND) and pin 18(IO: 24 in BCM) in BOARD numbering
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)


pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()
pygame.mixer.set_num_channels(32)


def parse_arguments(sysargs):
    """ Setup the command line options. """

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-p', '--piano', default='piano')
    parser.add_argument('-d', '--drums', default='drums2')

    return parser.parse_args(sysargs)


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]


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

    def __init__(self, sound_index):
        super(Piano, self).__init__(sound_index)

        pianohat.on_note(self.handle_note)
        pianohat.on_octave_up(self.handle_octave_up)
        pianohat.on_octave_down(self.handle_octave_down)
        pianohat.on_instrument(self.handle_instrument)

        pianohat.auto_leds(True)

    def load_sounds(self):
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
            self.load_sounds()

    def handle_octave_up(self, channel, pressed):
        print("up octaves/octave")
        print(self.octaves)
        print(self.octave)
        if pressed and self.octave < int(self.octaves):
            self.octave += 1

    def handle_octave_down(self, channel, pressed):
        print("down octaves/octave")
        print(self.octaves)
        print(self.octave)
        if pressed and self.octave > 0:
            self.octave -= 1


def turn_off(pin):
    """ Shutdown the Raspberry Pi; the argument pin is not required
    but passed by event_detect. """

    GPIO.cleanup()
    subprocess.call(['sudo poweroff'], shell=True)


if __name__ == "__main__":
    # optional shutdown button
    GPIO.add_event_detect(24, edge=GPIO.FALLING, callback=turn_off) 
    args = parse_arguments(sys.argv[1:]) 

    drums = Drums(sound_sets.index(args.drums))
    piano = Piano(sound_sets.index(args.piano))

    signal.pause()


