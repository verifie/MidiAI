import rtmidi
import threading
import time

# ========== Complex African Polyrhythms MIDI Composer ==========

PORT_INDEX = 0
TEMPO_BPM = 120
SECONDS_PER_BEAT = 60.0 / TEMPO_BPM
VEL_MED = 100
CHANNEL = 9

# Advanced African Polyrhythmic Patterns
RHYTHMS = {
    "Cavacha": [(36,0),(38,0.5),(38,1),(36,1.5),(38,2),(38,2.5),(36,3),(38,3.5)],
    "Bikutsi": [(64,0),(64,0.5),(63,1),(63,1.5),(61,2),(61,2.5),(60,3),(60,3.5)],
    "Kpanlogo": [(64,0),(60,0.75),(63,1.5),(64,2.25),(60,3)],
    "Djole": [(61,0),(63,1),(64,2),(60,3)],
    "Bell Pattern": [(67,0),(67,0.75),(67,1.5),(67,2.25),(67,3),(67,3.5)]
}

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

class Rhythm(threading.Thread):
    def __init__(self, pattern, offset=0):
        super().__init__(daemon=True)
        self.pattern = pattern
        self.offset = offset
        self.scheduler = None

    def attach(self, scheduler):
        self.scheduler = scheduler

    def run(self):
        t = self.offset
        pattern_length = 4 * SECONDS_PER_BEAT
        while True:
            for note, beat in self.pattern:
                duration = 0.15 * SECONDS_PER_BEAT
                self.scheduler.schedule(t + beat * SECONDS_PER_BEAT, [0x99, note, VEL_MED])
                self.scheduler.schedule(t + beat * SECONDS_PER_BEAT + duration, [0x89, note, 0])
            t += pattern_length

# Main Program with Polyrhythmic Layers
def main():
    midiout = rtmidi.MidiOut()
    midiout.open_port(PORT_INDEX)
    scheduler = Scheduler(midiout)

    print("🥁 Playing Complex African Polyrhythms. Press Ctrl+C to stop.")

    # Start multiple rhythms simultaneously for polyrhythmic complexity
    rhythms = [
        Rhythm(RHYTHMS["Cavacha"], offset=0),
        Rhythm(RHYTHMS["Bikutsi"], offset=SECONDS_PER_BEAT),
        Rhythm(RHYTHMS["Kpanlogo"], offset=SECONDS_PER_BEAT * 0.5),
        Rhythm(RHYTHMS["Djole"], offset=SECONDS_PER_BEAT * 1.5),
        Rhythm(RHYTHMS["Bell Pattern"], offset=0)
    ]

    for rhythm in rhythms:
        rhythm.attach(scheduler)
        rhythm.start()

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