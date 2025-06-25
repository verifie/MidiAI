import rtmidi
import threading
import time

# ========== African Drums MIDI Composer with Menu ========== 

PORT_INDEX = 0
TEMPO_BPM = 120
SECONDS_PER_BEAT = 60.0 / TEMPO_BPM
VEL_MED = 100
CHANNEL = 9

# Rhythm Patterns (General MIDI Drum)
RHYTHMS = {
    "Cavacha": [(36,0),(38,0.5),(42,0.25),(42,0.75)],
    "Bikutsi": [(64,0),(63,0.33),(61,0.66),(60,1)],
    "Kpanlogo": [(64,0),(60,0.5),(63,0.75),(64,1)],
    "Djole": [(61,0),(63,0.5),(64,0.75),(60,1)],
    "Bell Pattern": [(67,0),(67,0.5),(67,1),(67,1.5),(67,2),(67,2.5),(67,3)]
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
    def __init__(self, pattern):
        super().__init__(daemon=True)
        self.pattern = pattern
        self.scheduler = None

    def attach(self, scheduler):
        self.scheduler = scheduler

    def run(self):
        t = 0
        while True:
            for note, beat in self.pattern:
                duration = 0.2 * SECONDS_PER_BEAT
                self.scheduler.schedule(t + beat * SECONDS_PER_BEAT, [0x99, note, VEL_MED])
                self.scheduler.schedule(t + beat * SECONDS_PER_BEAT + duration, [0x89, note, 0])
            t += 4 * SECONDS_PER_BEAT

# Main Program
def main():
    midiout = rtmidi.MidiOut()
    midiout.open_port(PORT_INDEX)
    scheduler = Scheduler(midiout)

    print("Choose an African rhythm to play:")
    for idx, name in enumerate(RHYTHMS.keys(), 1):
        print(f"{idx}. {name}")

    choice = int(input("Enter rhythm number: "))
    rhythm_name = list(RHYTHMS.keys())[choice - 1]
    rhythm = Rhythm(RHYTHMS[rhythm_name])
    rhythm.attach(scheduler)
    rhythm.start()

    print(f"🥁 Playing {rhythm_name} Rhythm. Press Ctrl+C to stop.")
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
