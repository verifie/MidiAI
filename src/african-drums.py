import rtmidi
import threading
import time
import random

# ========== African Drums MIDI Composer ==========

PORT_INDEX = 0
TEMPO_BPM = 120
SECONDS_PER_BEAT = 60.0 / TEMPO_BPM

# Velocity Levels
VEL_MED = 100

# MIDI Percussion Instruments (General MIDI Drum map)
DRUM_SOUNDS = [
    61,  # Low Bongo
    60,  # High Bongo
    63,  # Open Conga
    64,  # Low Conga
    65,  # High Timbale
    66,  # Low Timbale
    67,  # High Agogo
    68,  # Low Agogo
    69,  # Cabasa
    70,  # Maracas
    71,  # Short Whistle
    72   # Long Whistle
]

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

class Drums(threading.Thread):
    def __init__(self, channel):
        super().__init__(daemon=True)
        self.channel = channel
        self.scheduler = None

    def attach(self, scheduler):
        self.scheduler = scheduler

    def run(self):
        t = 0
        while True:
            complexity = random.choice([2, 4, 6, 8])
            for _ in range(complexity):
                drum_sound = random.choice(DRUM_SOUNDS)
                duration = random.choice([0.25, 0.5, 1]) * SECONDS_PER_BEAT
                self.scheduler.schedule(t, [0x99, drum_sound, VEL_MED])
                self.scheduler.schedule(t + duration, [0x89, drum_sound, 0])
                t += duration
            t += SECONDS_PER_BEAT

# Main Program

def main():
    midiout = rtmidi.MidiOut()
    midiout.open_port(PORT_INDEX)
    scheduler = Scheduler(midiout)

    drums = Drums(channel=9)
    drums.attach(scheduler)
    drums.start()

    print("🥁 African Drums MIDI Composer Running. Press Ctrl+C to stop.")
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
