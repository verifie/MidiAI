import rtmidi
import time
import threading
import random
from collections import deque

# ========== Configuration ==========
PORT_INDEX = 0       # MIDI port index
TEMPO_BPM = 80       # Slightly faster for interest
SECONDS_PER_BEAT = 60.0 / TEMPO_BPM

# MIDI channels
CHANNELS = {
    'soprano': 0,
    'alto':    1,
    'tenor':   2,
    'bass':    3,
    'accomp':  4
}

PIANO_PROGRAM = 0    # Acoustic Grand Piano

# Humanization parameters
TIMING_VAR = 0.02    # up to ±20ms
VEL_VAR    = 8       # up to ±8 velocity
PHRASE_GAP = 0.5     # beats between motif repeats

# Scale and chords (C major)
SCALE_NOTES = [60, 62, 64, 65, 67, 69, 71]
CHORD_SEQUENCE = [
    [0, 4, 7],   # I
    [2, 5, 9],   # ii
    [4, 7, 11],  # iii
    [5, 9, 0],   # IV
    [7, 11, 2],  # V
    [9, 0, 4],   # vi
    [11,2,5],    # vii°
    [0, 7, 4]    # inversion back to I
]

# Pre-defined soprano motifs (scale-degree, duration)
SOPRANO_MOTIFS = [
    [(0,1),(2,0.5),(4,0.5),(5,1)],
    [(7,1),(5,0.5),(4,0.5),(2,1)],
    [(4,1),(2,1),(0,2)],
    [(5,0.5),(7,0.5),(9,1),(7,1)]
]

# Voice class to schedule events
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
            if wait>0:
                time.sleep(wait)
            # note on
            self.midiout.send_message([0x90 | self.channel, note, vel])
            # schedule note off in separate timer
            threading.Timer(dur, self.midiout.send_message,
                            args=([0x80 | self.channel, note, 0],)).start()

# ========== Event Generators ==========

START_TIME = time.time() + 1.0  # start after 1s

# Bass: root on each downbeat with rhythmic variation
def gen_bass():
    t = START_TIME
    while True:
        for chord in CHORD_SEQUENCE:
            root = chord[0] + 36
            for beat in [0,1.5,3]:
                dt = beat * SECONDS_PER_BEAT + random.uniform(-TIMING_VAR, TIMING_VAR)
                vel = 60 + random.randint(-VEL_VAR, VEL_VAR)
                yield (t + dt, root, 0.4 * SECONDS_PER_BEAT, vel)
            t += 4 * SECONDS_PER_BEAT

# Accompaniment: broken arpeggio over each chord
def gen_accomp():
    t = START_TIME
    while True:
        for chord in CHORD_SEQUENCE:
            notes = [n+48 for n in chord] + [chord[0]+60]
            positions = [0,0.5,1,1.5,2,2.5,3,3.5]
            for pos in positions:
                note = random.choice(notes)
                dt = pos * SECONDS_PER_BEAT + random.uniform(-TIMING_VAR, TIMING_VAR)
                vel = 50 + random.randint(-VEL_VAR, VEL_VAR)
                yield (t + dt, note, 0.3 * SECONDS_PER_BEAT, vel)
            t += 4 * SECONDS_PER_BEAT

# Soprano: motif sequence with transposition by chord
def gen_soprano():
    t = START_TIME
    motif_queue = deque(SOPRANO_MOTIFS)
    while True:
        for chord in CHORD_SEQUENCE:
            motif = motif_queue[0]
            motif_queue.rotate(-1)
            trans = chord[2]  # use top note of triad
            for degree,dur in motif:
                note = SCALE_NOTES[degree%len(SCALE_NOTES)] + (trans//12)*12
                dt = random.uniform(-TIMING_VAR, TIMING_VAR)
                vel = 70 + random.randint(-VEL_VAR, VEL_VAR)
                yield (t + dt, note, dur*SECONDS_PER_BEAT, vel)
                t += dur*SECONDS_PER_BEAT
            t += PHRASE_GAP * SECONDS_PER_BEAT

# Alto/Tenor: invert soprano motifs for simple counterpoint
def gen_counterpoint(offset_channel):
    def gen():
        t = START_TIME
        motif_queue = deque(SOPRANO_MOTIFS)
        while True:
            for chord in CHORD_SEQUENCE:
                motif = motif_queue[0]
                motif_queue.rotate(-1)
                for degree,dur in motif:
                    # invert around middle C
                    inv_degree = -degree
                    note = SCALE_NOTES[inv_degree%len(SCALE_NOTES)] + offset_channel*12
                    dt = random.uniform(-TIMING_VAR, TIMING_VAR)
                    vel = 65 + random.randint(-VEL_VAR, VEL_VAR)
                    yield (t + dt, note, dur*SECONDS_PER_BEAT, vel)
                    t += dur*SECONDS_PER_BEAT
                t += PHRASE_GAP * SECONDS_PER_BEAT
    return gen

# ========== Main Setup ==========

def open_midi():
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    if not ports:
        raise RuntimeError("No MIDI ports found.")
    midiout.open_port(PORT_INDEX)
    for ch in CHANNELS.values():
        midiout.send_message([0xC0|ch, PIANO_PROGRAM])
    return midiout

# Launch all voices
def main():
    midiout = open_midi()
    players = [
        VoicePlayer('bass',    midiout, gen_bass),
        VoicePlayer('accomp',  midiout, gen_accomp),
        VoicePlayer('soprano', midiout, gen_soprano),
        VoicePlayer('alto',    midiout, gen_counterpoint(4)),
        VoicePlayer('tenor',   midiout, gen_counterpoint(3)),
    ]
    for p in players:
        p.start()
    print("Complex contrapuntal texture running. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        midiout.close_port()

if __name__ == '__main__':
    main()
