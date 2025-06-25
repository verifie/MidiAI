import rtmidi
import threading
import time

# ========== 80s Synth-Pop MIDI Composer ==========

PORT_INDEX = 0
TEMPO_BPM = 125
SECONDS_PER_BEAT = 60.0 / TEMPO_BPM

# Velocity Levels
VEL_SOFT = 60
VEL_MED = 90
VEL_LOUD = 120

# 80s MIDI Instruments (Microsoft GS Wavetable Synth)
INSTRUMENTS = {
    'pad': 89,            # New Age Pad
    'electric_piano': 4,  # Electric Piano 1
    'synth_bass': 38,     # Synth Bass 1
    'square_lead': 80,    # Square Lead
    'synth_arpeggio': 82  # Synth Bass 2
}

# Channel Assignments (0-based indexing)
CHANNELS = {
    'drums': 9,
    'bass': 1,
    'chords': 2,
    'arpeggio': 3,
    'lead': 4,
    'pad': 5
}

# Drum Pattern
DRUM_MAP = {'kick': 36, 'hat_closed': 42, 'snare': 38}
DRUM_PATTERN = [(DRUM_MAP['kick'], 0),
                (DRUM_MAP['hat_closed'], 0),
                (DRUM_MAP['hat_closed'], 0.5),
                (DRUM_MAP['snare'], 1)]

# Chord Progression (I-V-vi-IV in C)
CHORDS = [[60, 64, 67], [67, 71, 74], [69, 72, 76], [65, 69, 72]]
ARPEG_SEQ = [0, 1, 2, 1]
LEAD_MOTIFS = [[0, 2, 4, 5, 4, 2], [4, 5, 7, 9, 7, 5], [7, 9, 12, 9, 7, 5]]

# Scheduler Class
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

# Part Class
class Part(threading.Thread):
    def __init__(self, gen_fn, channel, program=None):
        super().__init__(daemon=True)
        self.gen = gen_fn()
        self.channel = channel
        self.program = program
        self.scheduler = None

    def attach(self, scheduler):
        self.scheduler = scheduler
        if self.program is not None:
            self.scheduler.schedule(0, [0xC0 | self.channel, self.program])

    def run(self):
        for t, note, dur, vel in self.gen:
            self.scheduler.schedule(t, [0x90 | self.channel, note, vel])
            self.scheduler.schedule(t + dur, [0x80 | self.channel, note, 0])

# Generators

# Drums
def gen_drums():
    t = 0
    while True:
        for note, beat in DRUM_PATTERN:
            yield t + beat * SECONDS_PER_BEAT, note, 0.1, VEL_LOUD
        t += 4 * SECONDS_PER_BEAT

# Synth Bass
def gen_bass():
    t = 0
    while True:
        for chord in CHORDS:
            yield t, chord[0] - 12, 1 * SECONDS_PER_BEAT, VEL_MED
            t += 2 * SECONDS_PER_BEAT

# Electric Piano Chords
def gen_chords():
    t = 0
    while True:
        for chord in CHORDS:
            for note in chord:
                yield t, note, 4 * SECONDS_PER_BEAT, VEL_SOFT
            t += 4 * SECONDS_PER_BEAT

# Synth Arpeggio
def gen_arpeggio():
    t = 0
    while True:
        for chord in CHORDS:
            for i in ARPEG_SEQ:
                yield t, chord[i], 0.25 * SECONDS_PER_BEAT, VEL_MED
                t += 0.25 * SECONDS_PER_BEAT

# Square Lead Melody
def gen_lead():
    t = 0
    motifs = LEAD_MOTIFS.copy()
    while True:
        motif = motifs.pop(0)
        motifs.append(motif)
        for deg in motif:
            yield t, 72 + deg, 0.5 * SECONDS_PER_BEAT, VEL_LOUD
            t += 0.5 * SECONDS_PER_BEAT
        t += 0.5 * SECONDS_PER_BEAT

# Synth Pad
def gen_pad():
    t = 0
    while True:
        for chord in CHORDS:
            for note in chord:
                yield t, note, 4 * SECONDS_PER_BEAT, VEL_SOFT
            t += 4 * SECONDS_PER_BEAT

# Main Program

def main():
    midiout = rtmidi.MidiOut()
    midiout.open_port(PORT_INDEX)
    scheduler = Scheduler(midiout)

    parts = [
        Part(gen_drums, CHANNELS['drums']),
        Part(gen_bass, CHANNELS['bass'], INSTRUMENTS['synth_bass']),
        Part(gen_chords, CHANNELS['chords'], INSTRUMENTS['electric_piano']),
        Part(gen_arpeggio, CHANNELS['arpeggio'], INSTRUMENTS['synth_arpeggio']),
        Part(gen_lead, CHANNELS['lead'], INSTRUMENTS['square_lead']),
        Part(gen_pad, CHANNELS['pad'], INSTRUMENTS['pad'])
    ]

    for p in parts:
        p.attach(scheduler)
        p.start()

    print("🎹 80s Synth-Pop MIDI Composer Running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping MIDI Composer.")
        for ch in range(16):
            midiout.send_message([0xB0 | ch, 123, 0])  # All notes off
        midiout.close_port()

if __name__ == '__main__':
    main()