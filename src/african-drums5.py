import rtmidi
import threading
import time
import sys

# Platform-specific module for single-key press detection
try:
    # Windows
    import msvcrt
    def get_key():
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8').lower()
        return None
except ImportError:
    # Unix-like (Linux, macOS)
    import tty
    import termios
    def get_key():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# ================================== MIDI and Timing Configuration ==================================

# --- Select your MIDI output port ---
# Use rtmidi.MidiOut().get_ports() to see available ports and change the index.
# A virtual synth like "Microsoft GS Wavetable Synth" on Windows or SimpleSynth on macOS will work.
PORT_INDEX = 0 
TEMPO_BPM = 120
VEL_ACCENT = 120
VEL_NORMAL = 100
VEL_GHOST = 70
DRUM_CHANNEL = 9  # MIDI channel 10 is 9 in 0-indexed notation

# ================================== RHYTHM DEFINITIONS ==================================
#
# Each rhythm is a dictionary of instrumental parts.
# Each part is a list of tuples: (beat, midi_note, velocity, duration_in_beats)
# This structure allows for complex, multi-instrument polyrhythms.
# Standard General MIDI (GM) Drum Map notes are used.
#

AFRICAN_RHYTHMS = {
    "1": {
        "name": "Fanga (Liberia/Guinea)",
        "bpm": 130,
        "beats_per_measure": 4,
        "parts": {
            "Dundun": [ # Low Tom: 45
                (0, 45, VEL_ACCENT, 0.5),
                (2, 45, VEL_ACCENT, 0.5),
            ],
            "Sangban": [ # Mid Tom: 47
                (1, 47, VEL_NORMAL, 0.25),
                (3, 47, VEL_NORMAL, 0.25),
            ],
            "Kenkeni (Bell)": [ # Cowbell: 56
                (0, 56, VEL_NORMAL, 0.1), (0.5, 56, VEL_GHOST, 0.1),
                (1, 56, VEL_NORMAL, 0.1), (1.5, 56, VEL_GHOST, 0.1),
                (2, 56, VEL_NORMAL, 0.1), (2.5, 56, VEL_GHOST, 0.1),
                (3, 56, VEL_NORMAL, 0.1), (3.5, 56, VEL_GHOST, 0.1),
            ],
            "Djembe": [ # High Bongo/Low Conga: 60/63
                (0.75, 60, VEL_NORMAL, 0.1),
                (1.5, 63, VEL_ACCENT, 0.1),
                (2.75, 60, VEL_NORMAL, 0.1),
                (3.25, 63, VEL_NORMAL, 0.1),
                (3.75, 63, VEL_ACCENT, 0.1),
            ]
        }
    },
    "2": {
        "name": "Agbekor (Ewe - Ghana)",
        "bpm": 110,
        "beats_per_measure": 12, # This is in 12/8 time
        "parts": {
            "Gankogui (Bell)": [ # High/Low Agogo: 67/68
                (0, 67, VEL_ACCENT, 0.5), (2, 68, VEL_NORMAL, 0.5),
                (3, 67, VEL_ACCENT, 0.5), (5, 68, VEL_NORMAL, 0.5),
                (6, 67, VEL_ACCENT, 0.5), (7, 68, VEL_NORMAL, 0.5),
                (9, 68, VEL_NORMAL, 0.5), (10, 67, VEL_ACCENT, 0.5),
            ],
            "Axatse (Shaker)": [ # Maracas: 70
                (0, 70, VEL_NORMAL, 0.2), (3, 70, VEL_NORMAL, 0.2),
                (6, 70, VEL_NORMAL, 0.2), (9, 70, VEL_NORMAL, 0.2),
            ],
            "Kagan (Drum)": [ # High Conga: 62
                (1, 62, VEL_NORMAL, 0.2), (2, 62, VEL_GHOST, 0.2),
                (4, 62, VEL_NORMAL, 0.2), (5, 62, VEL_GHOST, 0.2),
                (7, 62, VEL_NORMAL, 0.2), (8, 62, VEL_GHOST, 0.2),
                (10, 62, VEL_NORMAL, 0.2), (11, 62, VEL_GHOST, 0.2),
            ]
        }
    },
    "3": {
        "name": "Kpanlogo (Ga - Ghana)",
        "bpm": 125,
        "beats_per_measure": 4,
        "parts": {
            "Bell": [ # Cowbell: 56
                (0, 56, VEL_ACCENT, 0.2),
                (1, 56, VEL_NORMAL, 0.2),
                (1.5, 56, VEL_NORMAL, 0.2),
                (2.5, 56, VEL_ACCENT, 0.2),
                (3, 56, VEL_NORMAL, 0.2),
            ],
            "Conga 1": [ # Mute/Open High Conga: 65/62
                (0, 62, VEL_ACCENT, 0.2),
                (2, 62, VEL_ACCENT, 0.2),
                (3.5, 62, VEL_ACCENT, 0.2),
            ],
            "Conga 2": [
                (1, 65, VEL_NORMAL, 0.2),
                (1.5, 62, VEL_GHOST, 0.2),
                (3, 65, VEL_NORMAL, 0.2),
            ]
        }
    }
}


# ================================== High-Precision MIDI Scheduler ==================================

class MidiScheduler(threading.Thread):
    """
    A high-precision scheduler that sends MIDI events at the correct time.
    It calculates the exact time until the next event and sleeps for that duration,
    making it more accurate than a fixed-sleep loop.
    """
    def __init__(self, midiout):
        super().__init__(daemon=True)
        self.midiout = midiout
        self.events = []
        self.lock = threading.Lock()
        self.running = threading.Event()
        self.running.set()

    def schedule_event(self, play_time, msg):
        """Schedules a MIDI message to be sent at a specific monotonic time."""
        with self.lock:
            self.events.append((play_time, msg))
            self.events.sort() # Keep events sorted by time

    def run(self):
        while self.running.is_set():
            now = time.monotonic()
            
            with self.lock:
                if not self.events:
                    # If no events, sleep for a short while to avoid busy-waiting
                    sleep_time = 0.005
                else:
                    next_event_time = self.events[0][0]
                    if next_event_time <= now:
                        # Event is due, send it
                        _, msg = self.events.pop(0)
                        self.midiout.send_message(msg)
                        continue # Check for next event immediately
                    else:
                        # Event is in the future, sleep until it's due
                        sleep_time = next_event_time - now
            
            time.sleep(max(0, sleep_time))

    def stop(self):
        self.running.clear()

# ================================== Rhythm Player Thread ==================================

class RhythmPlayer(threading.Thread):
    """
    A thread that plays a selected multi-part rhythm in a loop.
    It calculates the precise timing for each note and schedules it.
    """
    def __init__(self, scheduler, rhythm_data):
        super().__init__(daemon=True)
        self.scheduler = scheduler
        self.rhythm = rhythm_data
        self.stop_event = threading.Event()

    def run(self):
        seconds_per_beat = 60.0 / self.rhythm['bpm']
        measure_duration_secs = self.rhythm['beats_per_measure'] * seconds_per_beat
        start_time = time.monotonic()
        cycle = 0

        while not self.stop_event.is_set():
            loop_time = start_time + (cycle * measure_duration_secs)
            
            # Schedule all notes for the current loop iteration
            for part_name, part_notes in self.rhythm['parts'].items():
                for beat, note, velocity, duration in part_notes:
                    note_on_time = loop_time + (beat * seconds_per_beat)
                    note_off_time = note_on_time + (duration * seconds_per_beat)
                    
                    # Schedule Note On
                    self.scheduler.schedule_event(note_on_time, [0x90 | DRUM_CHANNEL, note, velocity])
                    # Schedule Note Off
                    self.scheduler.schedule_event(note_off_time, [0x80 | DRUM_CHANNEL, note, 0])

            cycle += 1
            # Sleep until the start of the next measure to avoid flooding the scheduler
            next_loop_start = start_time + (cycle * measure_duration_secs)
            sleep_duration = next_loop_start - time.monotonic()
            if sleep_duration > 0:
                time.sleep(sleep_duration)

    def stop(self):
        self.stop_event.set()

# ================================== Main Application ==================================

def display_menu():
    """Prints the main menu."""
    print("\n" + "="*40)
    print("      AFRICAN RHYTHM MIDI PLAYER")
    print("="*40)
    for key, val in AFRICAN_RHYTHMS.items():
        print(f"  [{key}] {val['name']} ({val['bpm']} BPM)")
    print("\n  [r] Return to this menu")
    print("  [q] Quit")
    print("-"*40)

def silence_all_notes(midiout):
    """Sends 'All Notes Off' messages to all channels to prevent stuck notes."""
    for ch in range(16):
        midiout.send_message([0xB0 | ch, 123, 0]) # All notes off
    print("All notes silenced.")


def main():
    """Main application loop."""
    midiout = rtmidi.MidiOut()
    try:
        midiout.open_port(PORT_INDEX)
    except (rtmidi.InvalidPortError, rtmidi.NoPortsAvailableError):
        print(f"Error: MIDI Port {PORT_INDEX} not available.")
        print("Available ports:", midiout.get_ports())
        return

    scheduler = MidiScheduler(midiout)
    scheduler.start()
    
    active_player = None

    try:
        display_menu()
        while True:
            key = get_key()
            if key:
                if key == 'q':
                    print("Quitting...")
                    break
                
                if key == 'r':
                    if active_player:
                        print("Stopping current rhythm...")
                        active_player.stop()
                        active_player.join()
                        active_player = None
                        silence_all_notes(midiout)
                    display_menu()

                elif key in AFRICAN_RHYTHMS:
                    if active_player:
                        active_player.stop()
                        active_player.join()
                        silence_all_notes(midiout)
                    
                    rhythm_data = AFRICAN_RHYTHMS[key]
                    print(f"Playing '{rhythm_data['name']}'... (Press 'r' to return to menu)")
                    active_player = RhythmPlayer(scheduler, rhythm_data)
                    active_player.start()
            
            time.sleep(0.01) # Small sleep to prevent high CPU usage in the main loop

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        if active_player:
            active_player.stop()
        scheduler.stop()
        if midiout.is_port_open():
            silence_all_notes(midiout)
            midiout.close_port()
            print("MIDI port closed. Goodbye!")

if __name__ == '__main__':
    main()