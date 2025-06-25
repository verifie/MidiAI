import rtmidi
import threading
import time

# MIDI Setup
PORT_INDEX = 0
TEMPO_BPM = 70
SECONDS_PER_BEAT = 60 / TEMPO_BPM
CHANNELS = {'soprano': 0, 'alto': 1, 'tenor': 2, 'bass': 3, 'accomp': 4}
PIANO_PROGRAM = 0

# Velocity settings
VEL_SOFT = 55
VEL_MEDIUM = 70
VEL_LOUD = 85

# Beethoven-inspired structured themes (9th & 7th Symphony)
SYMPHONY_STRUCTURE = [
    ('soprano', 72, [(0,1),(4,1),(7,2),(12,1),(7,1),(4,2)], VEL_LOUD, 0),      # Joyful opening
    ('alto', 67, [(0,2),(2,1),(3,1),(5,2),(3,1),(2,1)], VEL_MEDIUM, 8),        # Reflective
    ('tenor', 64, [(7,1),(5,1),(4,2),(2,1),(0,2)], VEL_SOFT, 16),              # Thoughtful
    ('bass', 48, [(5,1),(7,1),(9,1),(7,1),(5,1),(4,1),(2,2)], VEL_MEDIUM, 24), # Depth
    ('accomp', 55, [(0,1),(4,1),(7,1),(4,1),(0,1),(4,1),(7,2)], VEL_SOFT, 32)  # Harmony
]

class VoicePlayer(threading.Thread):
    def __init__(self, name, midiout, melody_events):
        super().__init__(daemon=True)
        self.name = name
        self.midiout = midiout
        self.channel = CHANNELS[name]
        self.melody_events = melody_events

    def run(self):
        for event in self.melody_events:
            abs_time, note, dur, vel = event
            now = time.time()
            wait = abs_time - now
            if wait > 0:
                time.sleep(wait)
            self.midiout.send_message([0x90 | self.channel, note, vel])
            threading.Timer(dur, self.midiout.send_message,
                            args=([0x80 | self.channel, note, 0],)).start()

START_TIME = time.time() + 2

# Generate structured, non-overlapping symphony
def generate_voice_events(start_delay, base_note, motif, velocity):
    events = []
    current_time = START_TIME + (start_delay * SECONDS_PER_BEAT)
    for degree, duration in motif:
        note = base_note + degree
        events.append((current_time, note, duration * SECONDS_PER_BEAT, velocity))
        current_time += duration * SECONDS_PER_BEAT
    return events

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

    voices = []
    for voice_name, base_note, motif, velocity, delay in SYMPHONY_STRUCTURE:
        melody_events = generate_voice_events(delay, base_note, motif, velocity)
        voices.append(VoicePlayer(voice_name, midiout, melody_events))

    for v in voices:
        v.start()

    print("Playing refined Beethoven-inspired piano symphony. Enjoy the clear melodic journey. Ctrl+C to stop.")
    try:
        time.sleep(180)  # Approximately 3 minutes
    except KeyboardInterrupt:
        print("Stopping performance...")
    finally:
        midiout.close_port()

if __name__ == '__main__':
    main()