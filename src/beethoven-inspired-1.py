import rtmidi
import threading
import random
import time
from collections import deque

# MIDI Setup
PORT_INDEX = 0
TEMPO_BPM_MODERATE = 70
SECONDS_PER_BEAT = 60 / TEMPO_BPM_MODERATE
CHANNELS = {'soprano': 0, 'alto': 1, 'tenor': 2, 'bass': 3, 'accomp': 4}
PIANO_PROGRAM = 0

# Velocity settings
VEL_SOFT = 60
VEL_MEDIUM = 70
VEL_LOUD = 85

# Beethoven's 9th inspired melodic patterns
BEETHOVEN_THEMES = [
    [(0,1),(4,1),(7,2),(12,1),(7,1),(4,2)],  # Joyful motif
    [(0,2),(2,1),(3,1),(5,2),(3,1),(2,1)],   # Thoughtful motif
    [(7,1),(5,1),(4,2),(2,1),(0,2)],          # Reflective motif
    [(5,1),(7,1),(9,1),(7,1),(5,1),(4,1),(2,2)] # Complex motif
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

# Melodic generation inspired by Beethoven's style
def generate_beethoven_melody(base_note, motif, velocity, tempo_multiplier=1):
    t = START_TIME
    spb = SECONDS_PER_BEAT / tempo_multiplier
    total_duration = 0
    while total_duration < 300:  # Approximately 5 minutes
        for degree, dur in motif:
            note = base_note + degree
            yield (t, note, dur * spb, velocity)
            t += dur * spb
            total_duration += dur * spb
        motif = random.choice(BEETHOVEN_THEMES)

# MIDI Initialization
def open_midi():
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    if not ports:
        raise RuntimeError("No MIDI ports found.")
    midiout.open_port(PORT_INDEX)
    for ch in CHANNELS.values():
        midiout.send_message([0xC0|ch, PIANO_PROGRAM])
    return midiout

# Main execution
def main():
    midiout = open_midi()

    voices = [
        VoicePlayer('soprano', midiout, lambda: generate_beethoven_melody(72, BEETHOVEN_THEMES[0], VEL_LOUD, 1)),
        VoicePlayer('alto', midiout, lambda: generate_beethoven_melody(67, BEETHOVEN_THEMES[1], VEL_MEDIUM, 1.2)),
        VoicePlayer('tenor', midiout, lambda: generate_beethoven_melody(64, BEETHOVEN_THEMES[2], VEL_MEDIUM, 1)),
        VoicePlayer('bass', midiout, lambda: generate_beethoven_melody(48, BEETHOVEN_THEMES[3], VEL_SOFT, 0.8)),
        VoicePlayer('accomp', midiout, lambda: generate_beethoven_melody(55, random.choice(BEETHOVEN_THEMES), VEL_MEDIUM, 1.1))
    ]

    for v in voices:
        v.start()

    print("Playing Beethoven's 9th inspired piano symphony. Enjoy the performance. Ctrl+C to stop.")
    try:
        time.sleep(300)  # Play for approximately 5 minutes
    except KeyboardInterrupt:
        print("Stopping performance...")
    finally:
        midiout.close_port()

if __name__ == '__main__':
    main()
