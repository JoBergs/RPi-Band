#!/usr/bin/env python3

import subprocess
import pygame
import signal
import glob
import os
import re
import argparse
import sys

import drumhat
import pianohat
import RPi.GPIO as GPIO
import time

DESCRIPTION = '''This script integrates Pimoronis Piano HAT and Drum HAT software and gives you simple, 
ready-to-play instruments which use .wav files located in sounds.
The parameter -p expects the name of the directory containing the sounds that should be loaded onto the piano 
and -d expects the name of the directory containing the sounds that should be loaded onto the drums .

Press CTRL+C to exit.'''

GPIO.setmode(GPIO.BCM)

# safe shutdown button is pin 14 (GND) and pin 18(IO: 24 in BCM) in BOARD numbering
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# sound loader:
#   make a list of dirs
#   preload from CLI
#   stay constant for drums, iterate over for piano



PIANO_BANK = os.path.join(os.path.dirname(__file__), "sounds/")
DRUM_BANK = os.path.join(os.path.dirname(__file__), "sounds/drums2")

def parse_arguments(sysargs):
    """ Setup the command line options. """

    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('-p', '--piano', default='piano')
    parser.add_argument('-d', '--drums', default='drums2')

    return parser.parse_args(sysargs)

# move into init
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()
pygame.mixer.set_num_channels(32)

# accept 8bit for the synthi, extend sound_sets by it but handle specially 
SOUND_BASEDIR = os.path.join(os.path.dirname(__file__), "sounds/")
sound_sets = glob.glob(os.path.join(SOUND_BASEDIR, "*"))

class Drums:
    sounds = []

    def __init__(self, args):
        sounds_path = glob.glob(os.path.join(SOUND_BASEDIR, args.drums, "*.wav"))
        self.sounds = [pygame.mixer.Sound(f) for f in sounds_path]
        drumhat.on_hit(drumhat.PADS, self.handle_hit)
        drumhat.on_release(drumhat.PADS, self.handle_release)

    def handle_hit(self, event):
        # event.channel is a zero based channel index for each pad
        # event.pad is the pad number from 1 to 8
        self.sounds[event.channel].play(loops=0)

    def handle_release(self):
        pass   


samples_piano = []
files_piano = []
octave = 0
octaves = 0

patches = glob.glob(os.path.join(PIANO_BANK, '*'))
patch_index = 1  # this is bad for selecting the piano; rethink sound management


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]


def load_samples(patch):
    global samples_piano, files_piano, octaves, octave

    files_piano = []
    print('Loading samples_piano from: {}'.format(patch))

    files_piano.extend(glob.glob(os.path.join(patch, "*.wav")))
    files_piano.sort(key=natural_sort_key)
    octaves = len(files_piano) / 12
    samples_piano = [pygame.mixer.Sound(sample) for sample in files_piano]
    octave = int(octaves / 2)


pianohat.auto_leds(True)


def handle_note(channel, pressed):
    channel = channel + (12 * octave)
    if channel < len(samples_piano) and pressed:
        print('Playing Sound: {}'.format(files_piano[channel]))
        samples_piano[channel].play(loops=0)


def handle_instrument(channel, pressed):
    global patch_index
    if pressed:
        patch_index += 1
        patch_index %= len(patches)
        print('Selecting Patch: {}'.format(patches[patch_index]))
        load_samples(patches[patch_index])


def handle_octave_up(channel, pressed):
    global octave
    if pressed and octave < octaves:
        octave += 1
        print('Selected Octave: {}'.format(octave))


def handle_octave_down(channel, pressed):
    global octave
    if pressed and octave > 0:
        octave -= 1
        print('Selected Octave: {}'.format(octave))

def start_band(args):
    pianohat.on_note(handle_note)
    pianohat.on_octave_up(handle_octave_up)
    pianohat.on_octave_down(handle_octave_down)
    pianohat.on_instrument(handle_instrument)

    load_samples(patches[patch_index])

    drums = Drums(args)

    # drumhat.on_hit(drumhat.PADS, handle_hit)
    # drumhat.on_release(drumhat.PADS, handle_release)

    signal.pause()

def turn_off(pin):
    """ Shutdown the Raspberry Pi; the argument pin is not required
    but passed by event_detect. """

    GPIO.cleanup()
    subprocess.call(['sudo poweroff'], shell=True)



if __name__ == "__main__":
    # optional shutdown button
    GPIO.add_event_detect(24, edge=GPIO.FALLING, callback=turn_off) 
    args = parse_arguments(sys.argv[1:]) 
    print(args)
    start_band(args)


