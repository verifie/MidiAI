import rtmidi
import threading
import time
import sys
import select
import random
from collections import defaultdict

# ========== 80s Synth-Pop Composition Engine ==========
PORT_INDEX = 0
TEMPO_BPM = 125                    # 80s dance tempo
SECONDS_PER_BEAT = 60.0 / TEMPO_BPM

# Velocity levels
VEL_SOFT = 60
VEL_MED  = 90
VEL_LOUD = 120

# GM Program numbers for classic 80s sounds
INSTRUMENTS = {
    'pad':        89,   # New Age Pad
    'electric_piano': 4,    # Electric Piano 1
    'synth_bass': 38,   # Synth Bass 1
    'lead':       80,   # Square Lead
    'arpeggio':   82    # Synth Bass 2
}

# Channel assignments (0-based)
CHANNELS = {
    'drums':     9,  # channel 10 for GM drums
    'bass':      1,
    'chords':    2,
    'arpeggio':  3,
    'lead':      4,
    'pad':       5
}

# Section structure: verse, chorus, bridge
SECTIONS = [
    ('Intro', 8),
    ('Verse', 16),
    ('Chorus', 16),
    ('Verse', 16),
    ('Chorus', 16),
    ('Bridge', 8),
    ('Chorus', 16),
    ('Outro', 8)
]

# Simple drum pattern: four-on-the-floor + offbeat hat
DRUM_MAP = {
    'kick':36, 'hat_closed':42, 'snare':38
}
DRUM_PATTERN = [(DRUM_MAP['kick'],0),(DRUM_MAP['hat_closed'],0),
                (DRUM_MAP['hat_closed'],0.5),(DRUM_MAP['snare'],1)]

# Chord progression: I–V–vi–IV in C major
CHORDS = [[60,64,67],[67,71,74],[69,72,76],[65,69,72]]

# Arpeggio pattern (sixteenth-note)
ARPEG_SEQ = [0,1,2,1]

# Lead melody motifs (scale degrees)
LEAD_MOTIFS = [[0,2,4,5,4,2],[4,5,7,9,7,5],[7,9,12,9,7,5]]

class Scheduler:
    def __init__(self, midiout):
        self.midiout = midiout
        self.events = []
        self.lock = threading.Lock()
        threading.Thread(target=self.run, daemon=True).start()
    def schedule(self, delay, msg):
        play_time = time.time() + delay
        with self.lock:
            self.events.append((play_time, msg))
    def run(self):
        while True:
            now = time.time()
            with self.lock:
                due = [e for e in self.events if e[0] <= now]
                self.events = [e for e in self.events if e[0] > now]
            for _, msg in due:
                self.midiout.send_message(msg)
            time.sleep(0.001)

class Part(threading.Thread):
    def __init__(self, name, gen_fn, channel, program):
        super().__init__(daemon=True)
        self.name = name
        self.gen = gen_fn()
        self.channel = channel
        self.program = program
        self.scheduler = None
    def attach(self, scheduler):
        self.scheduler = scheduler
        # Program change
        if self.program is not None:
            self.scheduler.schedule(0, [0xC0|self.channel, self.program])
    def run(self):
        for t,note,dur,vel in self.gen:
            self.scheduler.schedule(t, [0x90|self.channel, note, vel])
            self.scheduler.schedule(t+dur, [0x80|self.channel, note, 0])

# Generators

def gen_drums():
    t=0
    while True:
        for note,beat in DRUM_PATTERN:
            t = beat*SECONDS_PER_BEAT + t
            yield t, note, 0.05, VEL_LOUD
        t += 4*SECONDS_PER_BEAT


def gen_bass():
    t=0
    while True:
        for chord in CHORDS:
            root=chord[0]-12
            yield t, root, 1*SECONDS_PER_BEAT, VEL_MED
            t += 2*SECONDS_PER_BEAT
        t += 0


def gen_chords():
    t=0
    while True:
        for chord in CHORDS:
            for note in chord:
                yield t, note, 4*SECONDS_PER_BEAT, VEL_SOFT
            t += 4*SECONDS_PER_BEAT


def gen_arpeggio():
    t=0
    while True:
        for chord in CHORDS:
            for i in ARPEG_SEQ:
                yield t, chord[i], 0.25*SECONDS_PER_BEAT, VEL_MED
                t += 0.25*SECONDS_PER_BEAT


def gen_lead():
    t=0
    motifs = LEAD_MOTIFS.copy()
    while True:
        motif = motifs.pop(0)
        motifs.append(motif)
        for deg in motif:
            yield t, 60+deg, 0.5*SECONDS_PER_BEAT, VEL_LOUD
            t += 0.5*SECONDS_PER_BEAT
        t += 0.5*SECONDS_PER_BEAT


def gen_pad():
    t=0
    while True:
        for chord in CHORDS:
            for note in chord:
                yield t, note, 4*SECONDS_PER_BEAT, VEL_SOFT
            t += 4*SECONDS_PER_BEAT

# Main

def main():
    midiout = rtmidi.MidiOut()
    ports=midiout.get_ports()
    midiout.open_port(PORT_INDEX)
    sched=Scheduler(midiout)

    parts = [
        Part('drums',gen_drums,CHANNELS['drums'],None),
        Part('bass',gen_bass,CHANNELS['bass'],INSTRUMENTS['synth_bass']),
        Part('chords',gen_chords,CHANNELS['chords'],INSTRUMENTS['electric_piano']),
        Part('arpeggio',gen_arpeggio,CHANNELS['arpeggio'],INSTRUMENTS['arpeggio']),
        Part('lead',gen_lead,CHANNELS['lead'],INSTRUMENTS['lead']),
        Part('pad',gen_pad,CHANNELS['pad'],INSTRUMENTS['pad'])
    ]
    for p in parts:
        p.attach(sched)
        p.start()

    print("80s Synth-Pop Composer! Press Ctrl+C to quit.")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping…")
        for ch in range(16): midiout.send_message([0xB0|ch,123,0])
        midiout.close_port()

if __name__=='__main__':
    main()
