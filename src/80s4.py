import rtmidi
import threading
import time

# ========== Simple 80s Synth-Pop MIDI Composer ==========

PORT_INDEX = 0
TEMPO_BPM = 115
SECONDS_PER_BEAT = 60.0 / TEMPO_BPM

# Velocity Levels
VEL_MED = 90

# 80s MIDI Instruments
INSTRUMENTS = {
    'electric_piano': 4,  # Electric Piano 1
    'synth_bass': 38      # Synth Bass 1
}

# Channel Assignments
CHANNELS = {
    'bass': 1,
    'chords': 2
}

# Chord Progression (I-V-vi-IV in C)
CHORDS = [[60, 64, 67], [67, 71, 74], [69, 72, 76], [65, 69, 72]]

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

def gen_bass():
    t = 0
    while True:
        for chord in CHORDS:
            yield t, chord[0] - 12, 4 * SECONDS_PER_BEAT, VEL_MED
            t += 4 * SECONDS_PER_BEAT

def gen_chords():
    t = 0
    while True:
        for chord in CHORDS:
            for note in chord:
                yield t, note, 4 * SECONDS_PER_BEAT, VEL_MED
            t += 4 * SECONDS_PER_BEAT

# Main Program

def main():
    midiout = rtmidi.MidiOut()
    midiout.open_port(PORT_INDEX)
    scheduler = Scheduler(midiout)

    parts = [
        Part(gen_bass, CHANNELS['bass'], INSTRUMENTS['synth_bass']),
        Part(gen_chords, CHANNELS['chords'], INSTRUMENTS['electric_piano'])
    ]

    for p in parts:
        p.attach(scheduler)
        p.start()

    print("🎹 Simple 80s Synth-Pop MIDI Composer Running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping MIDI Composer.")
        for ch in range(16):
            midiout.send_message([0xB0 | ch, 123, 0])
        midiout.close_port()

if __name__ == '__main__':
    main()