#!/usr/bin/env python3

import subprocess
import pygame
import signal
import glob
import os
import re

import drumhat
import pianohat
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# button for turning on and off the rpi-band sits on pin 14 (GND) and pin 18(IO: 24 in BCM) in BOARD numbering
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)


PIANO_BANK = os.path.join(os.path.dirname(__file__), "sounds/")
DRUM_BANK = os.path.join(os.path.dirname(__file__), "sounds/drums2")


print("""
This script integrates Pimoronis Piano HAT and Drum HAT software and gives you simple, ready-to-play instruments which use .wav files_piano.

The Piano HAT needs directories of wav files_piano in:

{}

The Drum HAT needs directories of wav files_drum in:

{}

Drum Pads are mapped like so:

7 = Rim hit, 1 = Whistle, 2 = Clash
6 = Hat,     8 = Clap,   3 = Cowbell
      5 = Snare,   4 = Base

Press CTRL+C to exit.
""".format(PIANO_BANK, DRUM_BANK))

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()
pygame.mixer.set_num_channels(32)

######### DRUMS


files_drum = glob.glob(os.path.join(DRUM_BANK, "*.wav"))
files_drum.sort()

samples_drum = [pygame.mixer.Sound(f) for f in files_drum]


def handle_hit(event):
    # event.channel is a zero based channel index for each pad
    # event.pad is the pad number from 1 to 8
    samples_drum[event.channel].play(loops=0)
    print("You hit pad {}, playing: {}".format(event.pad,files_drum[event.channel]))

def handle_release():
    pass

drumhat.on_hit(drumhat.PADS, handle_hit)
drumhat.on_release(drumhat.PADS, handle_release)

######## /DRUMS

FILETYPES = ['*.wav', '*.ogg']
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
    for filetype in FILETYPES:
        files_piano.extend(glob.glob(os.path.join(patch, filetype)))
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

def start_band():
    pianohat.on_note(handle_note)
    pianohat.on_octave_up(handle_octave_up)
    pianohat.on_octave_down(handle_octave_down)
    pianohat.on_instrument(handle_instrument)

    load_samples(patches[patch_index])

    signal.pause()

def turn_off(pin):
    """ Shutdown the Raspberry Pi; the argument pin is not required
    but passed by event_detect. """

    GPIO.cleanup()
    subprocess.call(['sudo poweroff'], shell=True)



if __name__ == "__main__":
    # optional shutdown button
    GPIO.add_event_detect(24, edge=GPIO.FALLING, callback=turn_off)  
    start_band()


