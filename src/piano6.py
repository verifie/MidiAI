import rtmidi
import threading
import random
import time
from collections import deque

# MIDI Setup
PORT_INDEX = 0
TEMPO_BPM_SLOW = 55
TEMPO_BPM_FAST = 100
SECONDS_PER_BEAT_SLOW = 60 / TEMPO_BPM_SLOW
SECONDS_PER_BEAT_FAST = 60 / TEMPO_BPM_FAST
CHANNELS = {'soprano': 0, 'alto': 1, 'tenor': 2, 'bass': 3, 'accomp': 4}
PIANO_PROGRAM = 0

# Timing and velocity
TIMING_VAR = 0.02
VEL_VAR = 5
PHRASE_GAP = 1.0

# Comprehensive Classical Scales
CIRCLE_OF_FIFTHS_SCALES = [
    [60, 62, 64, 65, 67, 69, 71, 72],  # C major
    [67, 69, 71, 72, 74, 76, 78, 79],  # G major
    [62, 64, 66, 67, 69, 71, 73, 74],  # D major
    [69, 71, 73, 74, 76, 78, 80, 81],  # A major
    [64, 66, 68, 69, 71, 73, 75, 76],  # E major
]

# Melodic and rhythmic motifs
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

def generate_melody(scale, tempo, motif):
    t = START_TIME
    spb = 60 / tempo
    while True:
        for degree, dur in motif:
            note = scale[degree % len(scale)]
            yield (t, note, dur * spb, 70 + random.randint(-VEL_VAR, VEL_VAR))
            t += dur * spb
        t += PHRASE_GAP * spb

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
    scale_cycle = deque(CIRCLE_OF_FIFTHS_SCALES)

    voices = []
    for idx, voice_name in enumerate(['soprano', 'alto', 'tenor', 'bass', 'accomp']):
        scale = scale_cycle[0]
        motif = random.choice(CLASSICAL_MOTIFS)
        tempo = TEMPO_BPM_FAST if idx % 2 == 0 else TEMPO_BPM_SLOW
        voices.append(VoicePlayer(voice_name, midiout, lambda s=scale, t=tempo, m=motif: generate_melody(s, t, m)))
        scale_cycle.rotate(-1)

    for v in voices:
        v.start()

    print("Playing dynamically paced classical composition. Ctrl+C to stop.")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        midiout.close_port()

if __name__ == '__main__':
    main()