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

# It might be very impossible to run the drums and the 8bit synthi concurrently
# maybe on another core
# switching rates, even if very fast, is probably impossible
# BS, drums will just be 8bit then
# test switching the bitrate with mixer.quit(), then recreating it

# we need a different way for toggeling sine, square ect.: octave up/down needs to iterate over a list of all possible combinations


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

# sooooo.... what's better? make 8bit an own class that can't be changed with the instrument button?
# GOAL: create new instruments everytime the instrument button is pushed
#           that's the first step,
#           then make 8bit synthi an instrument

# would a tiny factory suffice?
#   

# rethink piano index management

class Container:
    """ Container is a factory for creating instruments, necessary for 
    switching to 8-bit piano """

    piano = None
    drums = None

    def __init__(self, piano_type, drums_type):
        self.drums = Drums(sound_sets.index(args.drums))
        self.create_piano(piano_type)

    def create_piano(self, piano_type):
        # This looks stupid. pass index instead? -> yes
        # nono static method is no good
        
        self.piano = Piano(self, sound_sets.index(args.piano))

        signal.pause()

# for now, i'll simply pass a reference to the container

# maybe add a wrapper four outputting played sound  filename?
class Piano(Instrument):
    octave = 0
    octaves = 0 
    container = None 

    def __init__(self, container, sound_index):
        self.container = container

        if sound_sets[sound_index] == '8bit':
            print("\n8bit!!!\n")
            set_mixer(MIXER_8BIT)
            pianohat.auto_leds(False)

        else:
            super(Piano, self).__init__(sound_index)

            pianohat.on_note(self.handle_note)
            pianohat.on_octave_up(self.handle_octave_up)
            pianohat.on_octave_down(self.handle_octave_down)
            pianohat.on_instrument(self.handle_instrument)

            pianohat.auto_leds(True)

    def load_sounds(self):
        set_mixer(MIXER_NORMAL)  # reset mixer to normal mode

        super(Piano, self).load_sounds()

        self.octaves = len(self.sounds) / 12
        self.octave = int(self.octaves / 2)   

    # could be merged with handle_hit in Drum, but that'd be obfuscating
    def handle_note(self, channel, pressed):
        channel = channel + (12 * self.octave)

        if channel < len(self.sounds) and pressed:
            self.sounds[channel].play(loops=0)

    def handle_instrument(self, channel, pressed):
        # this needs to call the parents function create_instruments

        # would be using a static method appropriate?

        # import ipdb
        # ipdb.set_trace()

        if pressed:
            self.sound_index = (self.sound_index + 1) % len(sound_sets)
            #self.container.
            
            # not necessary anymore, rethink
            self.load_sounds()

    def handle_octave_up(self, channel, pressed):
        if pressed and self.octave < int(self.octaves) - 1:
            self.octave += 1

    def handle_octave_down(self, channel, pressed):
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

    container = Container(sound_sets.index(args.drums), sound_sets.index(args.piano))
