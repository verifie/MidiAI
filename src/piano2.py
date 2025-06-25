import rtmidi
import threading
import random
import time
from collections import deque

# Configuration
PORT_INDEX = 0
TEMPO_BPM = 90
SECONDS_PER_BEAT = 60 / TEMPO_BPM

CHANNELS = {'soprano': 0, 'alto': 1, 'tenor': 2, 'bass': 3, 'accomp': 4}
PIANO_PROGRAM = 0

TIMING_VAR = 0.015
VEL_VAR = 8
PHRASE_GAP = 0.5

# Expanded scale (C major with accidentals)
SCALE_NOTES = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76]

# Enhanced classical chord progression (I-IV-V-I with variations)
CHORD_SEQUENCE = [
    [0, 4, 7], [5, 9, 0], [7, 11, 2], [0, 4, 7],   # I-IV-V-I
    [9, 0, 4], [2, 5, 9], [7, 11, 2], [0, 4, 7],   # vi-ii-V-I
    [5, 9, 0], [4, 7, 11], [7, 11, 2], [0, 4, 7]   # IV-iii-V-I
]

# Classical motifs with rhythmic complexity
SOPRANO_MOTIFS = [
    [(0,0.5),(2,0.5),(4,1),(7,0.5),(5,0.5)],
    [(7,1),(9,0.5),(7,0.5),(5,1)],
    [(4,0.5),(5,0.5),(7,0.5),(4,0.5),(2,1)],
    [(0,1),(4,0.5),(2,0.5),(0,1)]
]

class VoicePlayer(threading.Thread):
    def __init__(self, name, midiout, generate_events_fn):
        super().__init__(daemon=True)
        self.name = name
        self.midiout = midiout
        self.channel = CHANNELS[name]
        self.generate_events = generate_events_fn

    def run(self):
        for event in self.generate_events():
            abs_time, note, dur, vel = event
            now = time.time()
            wait = abs_time - now
            if wait > 0:
                time.sleep(wait)
            self.midiout.send_message([0x90 | self.channel, note, vel])
            threading.Timer(dur, self.midiout.send_message,
                            args=([0x80 | self.channel, note, 0],)).start()

START_TIME = time.time() + 1

def gen_bass():
    t = START_TIME
    while True:
        for chord in CHORD_SEQUENCE:
            root = chord[0] + 36
            rhythms = [0, 1, 2.5, 3]
            for beat in rhythms:
                yield (t + beat*SECONDS_PER_BEAT, root, 0.5*SECONDS_PER_BEAT, 60+random.randint(-VEL_VAR,VEL_VAR))
            t += 4*SECONDS_PER_BEAT

def gen_accomp():
    t = START_TIME
    while True:
        for chord in CHORD_SEQUENCE:
            notes = [n+48 for n in chord] + [chord[0]+60]
            pattern = [0,0.5,1,1.5,2,2.5,3,3.5]
            for pos in pattern:
                note = notes[int(pos*2)%len(notes)]
                yield (t+pos*SECONDS_PER_BEAT, note, 0.35*SECONDS_PER_BEAT, 55+random.randint(-VEL_VAR,VEL_VAR))
            t += 4*SECONDS_PER_BEAT

def gen_soprano():
    t = START_TIME
    motifs = deque(SOPRANO_MOTIFS)
    while True:
        for chord in CHORD_SEQUENCE:
            motif = motifs[0]
            motifs.rotate(-1)
            trans = chord[0]
            for degree, dur in motif:
                note = SCALE_NOTES[degree % len(SCALE_NOTES)] + trans
                yield (t, note, dur*SECONDS_PER_BEAT, 75+random.randint(-VEL_VAR,VEL_VAR))
                t += dur*SECONDS_PER_BEAT
            t += PHRASE_GAP*SECONDS_PER_BEAT

def gen_counterpoint(offset):
    def gen():
        t = START_TIME
        motifs = deque(SOPRANO_MOTIFS)
        while True:
            for chord in CHORD_SEQUENCE:
                motif = motifs[0]
                motifs.rotate(-1)
                trans = chord[1]
                for degree, dur in motif:
                    inv_degree = -degree
                    note = SCALE_NOTES[inv_degree % len(SCALE_NOTES)] + trans + offset
                    yield (t, note, dur*SECONDS_PER_BEAT, 70+random.randint(-VEL_VAR,VEL_VAR))
                    t += dur*SECONDS_PER_BEAT
                t += PHRASE_GAP*SECONDS_PER_BEAT
    return gen

def open_midi():
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    if not ports:
        raise RuntimeError("No MIDI ports found.")
    midiout.open_port(PORT_INDEX)
    for ch in CHANNELS.values():
        midiout.send_message([0xC0|ch, PIANO_PROGRAM])
    return midiout

def main():
    midiout = open_midi()
    voices = [
        VoicePlayer('bass', midiout, gen_bass),
        VoicePlayer('accomp', midiout, gen_accomp),
        VoicePlayer('soprano', midiout, gen_soprano),
        VoicePlayer('alto', midiout, gen_counterpoint(12)),
        VoicePlayer('tenor', midiout, gen_counterpoint(7)),
    ]
    for v in voices:
        v.start()
    print("Playing classical-inspired polyphony. Ctrl+C to stop.")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        midiout.close_port()

if __name__ == '__main__':
    main()
