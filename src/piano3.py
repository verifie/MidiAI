import rtmidi
import threading
import random
import time
from collections import deque

# Configuration
PORT_INDEX = 0
TEMPO_BPM = 85
SECONDS_PER_BEAT = 60 / TEMPO_BPM

CHANNELS = {'soprano': 0, 'alto': 1, 'tenor': 2, 'bass': 3, 'accomp': 4}
PIANO_PROGRAM = 0

TIMING_VAR = 0.02
VEL_VAR = 10
PHRASE_GAP = 0.75

# Classical Scale with Accidentals (C Major & harmonic minor)
SCALE_NOTES_MAJOR = [60, 62, 64, 65, 67, 69, 71, 72]
SCALE_NOTES_MINOR = [60, 62, 63, 65, 67, 68, 71, 72]

# Classical-inspired chord progressions (I-IV-V-I)
CHORD_SEQUENCE = [
    [0, 4, 7], [5, 9, 0], [7, 11, 2], [0, 4, 7],
    [2, 5, 9], [9, 0, 4], [7, 11, 2], [0, 4, 7]
]

# Melodic motifs inspired by Beethoven, Bach, Vivaldi
SOPRANO_MOTIFS = [
    [(0,0.5),(2,0.5),(4,1),(7,0.5),(5,1)],
    [(7,1),(6,0.5),(7,0.5),(5,1)],
    [(4,0.5),(5,0.5),(7,0.5),(4,0.5),(2,1)],
    [(0,1),(4,0.5),(2,0.5),(0,1.5)]
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
            rhythms = [0, 1.5, 3]
            for beat in rhythms:
                yield (t + beat*SECONDS_PER_BEAT, root, 0.6*SECONDS_PER_BEAT, 55+random.randint(-VEL_VAR,VEL_VAR))
            t += 4*SECONDS_PER_BEAT

def gen_accomp():
    t = START_TIME
    while True:
        for chord in CHORD_SEQUENCE:
            notes = [n+48 for n in chord] + [chord[0]+60]
            pattern = [0,1,1.5,2,2.5,3]
            for pos in pattern:
                note = notes[int(pos*2)%len(notes)]
                yield (t+pos*SECONDS_PER_BEAT, note, 0.4*SECONDS_PER_BEAT, 50+random.randint(-VEL_VAR,VEL_VAR))
            t += 4*SECONDS_PER_BEAT

def gen_soprano():
    t = START_TIME
    motifs = deque(SOPRANO_MOTIFS)
    scale = SCALE_NOTES_MAJOR
    while True:
        for chord in CHORD_SEQUENCE:
            motif = motifs[0]
            motifs.rotate(-1)
            trans = chord[0]
            for degree, dur in motif:
                note = scale[degree % len(scale)] + trans
                yield (t, note, dur*SECONDS_PER_BEAT, 80+random.randint(-VEL_VAR,VEL_VAR))
                t += dur*SECONDS_PER_BEAT
            t += PHRASE_GAP*SECONDS_PER_BEAT

def gen_counterpoint(offset, scale_type):
    def gen():
        t = START_TIME
        motifs = deque(SOPRANO_MOTIFS)
        scale = SCALE_NOTES_MINOR if scale_type == 'minor' else SCALE_NOTES_MAJOR
        while True:
            for chord in CHORD_SEQUENCE:
                motif = motifs[0]
                motifs.rotate(-1)
                trans = chord[1]
                for degree, dur in motif:
                    inv_degree = -degree
                    note = scale[inv_degree % len(scale)] + trans + offset
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
        VoicePlayer('alto', midiout, gen_counterpoint(12, 'major')),
        VoicePlayer('tenor', midiout, gen_counterpoint(7, 'minor')),
    ]
    for v in voices:
        v.start()
    print("Playing refined classical polyphony. Ctrl+C to stop.")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        midiout.close_port()

if __name__ == '__main__':
    main()