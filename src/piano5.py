import rtmidi
import threading
import random
import time
from collections import deque

# MIDI Setup
PORT_INDEX = 0
TEMPO_BPM = 60  # Slowed down for gentle appreciation
SECONDS_PER_BEAT = 60 / TEMPO_BPM
CHANNELS = {'soprano': 0, 'alto': 1, 'tenor': 2, 'bass': 3, 'accomp': 4}
PIANO_PROGRAM = 0

# Timing and velocity
TIMING_VAR = 0.02
VEL_VAR = 5
PHRASE_GAP = 1.0

# Comprehensive Classical Scales
SCALES = {
    'C_major': [60, 62, 64, 65, 67, 69, 71, 72],
    'A_minor': [57, 59, 60, 62, 64, 65, 68, 69],
    'G_major': [55, 57, 59, 60, 62, 64, 66, 67],
    'E_minor': [52, 54, 55, 57, 59, 60, 63, 64]
}

# Gentle Classical Chord Progressions
CLASSICAL_PROGRESSIONS = [
    [[0, 4, 7], [5, 9, 0], [7, 11, 2], [0, 4, 7]],
    [[0, 3, 7], [5, 8, 0], [7, 10, 2], [0, 3, 7]],
    [[0, 5, 9], [7, 11, 2], [5, 9, 0], [0, 4, 7]]
]

# Gentle Classical Motifs
CLASSICAL_MOTIFS = [
    [(0,1),(2,1),(4,2),(5,1),(4,1),(2,2)],
    [(7,1),(6,1),(5,1),(4,1),(3,2),(2,2)],
    [(4,1),(5,1),(7,2),(9,1),(7,1)],
    [(0,2),(2,1),(4,1),(5,3),(4,1),(2,1)],
    [(2,2),(4,1),(5,1),(7,2),(9,1),(7,1)],
    [(5,2),(4,1),(2,1),(0,3)],
    [(7,1),(9,1),(11,2),(9,1),(7,1)],
    [(0,1),(4,1),(7,2),(4,1),(0,1)]
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

# Voice Generation Functions for gentle intervals

def gen_bass(scale):
    t = START_TIME
    progression = random.choice(CLASSICAL_PROGRESSIONS)
    while True:
        for chord in progression:
            root = scale[chord[0] % len(scale)] - 24
            rhythms = [0, 2]
            for beat in rhythms:
                yield (t + beat*SECONDS_PER_BEAT, root, 1.0*SECONDS_PER_BEAT, 55)
            t += 4*SECONDS_PER_BEAT

def gen_accomp(scale):
    t = START_TIME
    progression = random.choice(CLASSICAL_PROGRESSIONS)
    while True:
        for chord in progression:
            notes = [scale[n % len(scale)] for n in chord]
            arpeggio_pattern = [0, 1, 2, 3]
            for pos in arpeggio_pattern:
                note = notes[pos % len(notes)]
                yield (t+pos*SECONDS_PER_BEAT, note, 0.8*SECONDS_PER_BEAT, 50)
            t += 4*SECONDS_PER_BEAT

def gen_soprano(scale):
    t = START_TIME
    motifs = deque(CLASSICAL_MOTIFS)
    progression = random.choice(CLASSICAL_PROGRESSIONS)
    while True:
        for chord in progression:
            motif = motifs[0]
            motifs.rotate(-1)
            transposition = scale[chord[0] % len(scale)]
            for degree, dur in motif:
                note = scale[degree % len(scale)] + transposition - 60
                yield (t, note, dur*SECONDS_PER_BEAT, 70)
                t += dur*SECONDS_PER_BEAT
            t += PHRASE_GAP*SECONDS_PER_BEAT

def gen_counterpoint(scale, offset):
    def gen():
        t = START_TIME
        motifs = deque(CLASSICAL_MOTIFS)
        progression = random.choice(CLASSICAL_PROGRESSIONS)
        while True:
            for chord in progression:
                motif = motifs[0]
                motifs.rotate(-1)
                transposition = scale[chord[1] % len(scale)]
                for degree, dur in motif:
                    inv_degree = (len(scale) - degree) % len(scale)
                    note = scale[inv_degree] + transposition + offset - 60
                    yield (t, note, dur*SECONDS_PER_BEAT, 65)
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
    selected_scale = random.choice(list(SCALES.values()))
    voices = [
        VoicePlayer('bass', midiout, lambda: gen_bass(selected_scale)),
        VoicePlayer('accomp', midiout, lambda: gen_accomp(selected_scale)),
        VoicePlayer('soprano', midiout, lambda: gen_soprano(selected_scale)),
        VoicePlayer('alto', midiout, lambda: gen_counterpoint(selected_scale, 12)()),
        VoicePlayer('tenor', midiout, lambda: gen_counterpoint(selected_scale, 7)()),
    ]
    for v in voices:
        v.start()
    print("Playing gentle classical composition. Ctrl+C to stop.")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        midiout.close_port()

if __name__ == '__main__':
    main()
