import rtmidi
import threading
import time

# MIDI Setup
PORT_INDEX = 0
TEMPO_BPM = 90
SECONDS_PER_BEAT = 60 / TEMPO_BPM
CHANNEL = 0
PIANO_PROGRAM = 0
VELOCITY = 70

# Mary Had a Little Lamb melody (MIDI note numbers)
MARY_MELODY = [
    (64, 1), (62, 1), (60, 1), (62, 1), (64, 1), (64, 1), (64, 2),
    (62, 1), (62, 1), (62, 2),
    (64, 1), (67, 1), (67, 2),
    (64, 1), (62, 1), (60, 1), (62, 1), (64, 1), (64, 1), (64, 1), (64, 1),
    (62, 1), (62, 1), (64, 1), (62, 1), (60, 4)
]

class MidiPlayer(threading.Thread):
    def __init__(self, midiout, melody_events):
        super().__init__(daemon=True)
        self.midiout = midiout
        self.melody_events = melody_events

    def run(self):
        for note, duration in self.melody_events:
            self.midiout.send_message([0x90 | CHANNEL, note, VELOCITY])
            time.sleep(duration * SECONDS_PER_BEAT)
            self.midiout.send_message([0x80 | CHANNEL, note, 0])

# MIDI Initialization
def open_midi():
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    if not ports:
        raise RuntimeError("No MIDI ports found.")
    midiout.open_port(PORT_INDEX)
    midiout.send_message([0xC0|CHANNEL, PIANO_PROGRAM])
    return midiout

# Main execution
def main():
    midiout = open_midi()
    player = MidiPlayer(midiout, MARY_MELODY)
    player.start()

    print("Playing 'Mary Had a Little Lamb'. Ctrl+C to stop.")
    try:
        player.join()
    except KeyboardInterrupt:
        print("Stopping performance...")
    finally:
        midiout.close_port()

if __name__ == '__main__':
    main()