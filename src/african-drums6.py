import rtmidi
import threading
import time
import sys
import random

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
VEL_ACCENT = 120
VEL_NORMAL = 100
VEL_GHOST = 70
DRUM_CHANNEL = 9  # MIDI channel 10 is 9 in 0-indexed notation

# ================================== RHYTHM & FILL DEFINITIONS ==================================
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
                (0, 45, VEL_ACCENT, 0.5), (2, 45, VEL_ACCENT, 0.5),
            ],
            "Sangban": [ # Mid Tom: 47
                (1, 47, VEL_NORMAL, 0.25), (3, 47, VEL_NORMAL, 0.25),
            ],
            "Kenkeni (Bell)": [ # Cowbell: 56
                (0, 56, VEL_NORMAL, 0.1), (0.5, 56, VEL_GHOST, 0.1),
                (1, 56, VEL_NORMAL, 0.1), (1.5, 56, VEL_GHOST, 0.1),
                (2, 56, VEL_NORMAL, 0.1), (2.5, 56, VEL_GHOST, 0.1),
                (3, 56, VEL_NORMAL, 0.1), (3.5, 56, VEL_GHOST, 0.1),
            ],
            "Djembe": [ # High Bongo/Low Conga: 60/63
                (0.75, 60, VEL_NORMAL, 0.1), (1.5, 63, VEL_ACCENT, 0.1),
                (2.75, 60, VEL_NORMAL, 0.1), (3.25, 63, VEL_NORMAL, 0.1),
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
                (0, 56, VEL_ACCENT, 0.2), (1, 56, VEL_NORMAL, 0.2),
                (1.5, 56, VEL_NORMAL, 0.2), (2.5, 56, VEL_ACCENT, 0.2),
                (3, 56, VEL_NORMAL, 0.2),
            ],
            "Conga 1": [ # Mute/Open High Conga: 65/62
                (0, 62, VEL_ACCENT, 0.2), (2, 62, VEL_ACCENT, 0.2),
                (3.5, 62, VEL_ACCENT, 0.2),
            ],
            "Conga 2": [
                (1, 65, VEL_NORMAL, 0.2), (1.5, 62, VEL_GHOST, 0.2),
                (3, 65, VEL_NORMAL, 0.2),
            ]
        }
    }
}

DRUM_FILLS = [
    [ # Simple Tom Roll (1 measure in 4/4)
        (0.0, 48, VEL_NORMAL, 0.2), (0.5, 47, VEL_NORMAL, 0.2),
        (1.0, 45, VEL_NORMAL, 0.2), (1.5, 43, VEL_NORMAL, 0.2),
        (2.0, 50, VEL_ACCENT, 0.2), (2.5, 48, VEL_NORMAL, 0.2),
        (3.0, 47, VEL_ACCENT, 0.2), (3.5, 45, VEL_ACCENT, 0.5),
    ],
    [ # Syncopated Snare/Conga
        (0.0, 38, VEL_NORMAL, 0.2), (0.75, 63, VEL_GHOST, 0.2),
        (1.5, 38, VEL_ACCENT, 0.2), (2.0, 64, VEL_NORMAL, 0.2),
        (2.5, 38, VEL_NORMAL, 0.2), (3.25, 63, VEL_ACCENT, 0.2),
    ]
]

# ================================== High-Precision MIDI Scheduler ==================================

class MidiScheduler(threading.Thread):
    def __init__(self, midiout):
        super().__init__(daemon=True)
        self.midiout = midiout
        self.events = []
        self.lock = threading.Lock()
        self.running = threading.Event()
        self.running.set()

    def schedule_event(self, play_time, msg):
        with self.lock:
            self.events.append((play_time, msg))
            self.events.sort()

    def run(self):
        while self.running.is_set():
            now = time.monotonic()
            with self.lock:
                if not self.events:
                    sleep_time = 0.005
                else:
                    next_event_time = self.events[0][0]
                    if next_event_time <= now:
                        _, msg = self.events.pop(0)
                        self.midiout.send_message(msg)
                        continue
                    else:
                        sleep_time = next_event_time - now
            time.sleep(max(0, sleep_time))

    def stop(self):
        self.running.clear()

# ================================== Rhythm Player Threads ==================================

class RhythmPlayer(threading.Thread):
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
            for _, part_notes in self.rhythm['parts'].items():
                for beat, note, velocity, duration in part_notes:
                    note_on_time = loop_time + (beat * seconds_per_beat)
                    note_off_time = note_on_time + (duration * seconds_per_beat)
                    self.scheduler.schedule_event(note_on_time, [0x90 | DRUM_CHANNEL, note, velocity])
                    self.scheduler.schedule_event(note_off_time, [0x80 | DRUM_CHANNEL, note, 0])
            cycle += 1
            next_loop_start = start_time + (cycle * measure_duration_secs)
            sleep_duration = next_loop_start - time.monotonic()
            if sleep_duration > 0:
                self.stop_event.wait(sleep_duration)

    def stop(self):
        self.stop_event.set()

class DynamicMixPlayer(threading.Thread):
    """A player that dynamically mixes two rhythms with breakdowns, buildups, and fills."""
    def __init__(self, scheduler, rhythm1_data, rhythm2_data):
        super().__init__(daemon=True)
        self.scheduler = scheduler
        self.rhythm1 = rhythm1_data
        self.rhythm2 = rhythm2_data
        self.stop_event = threading.Event()

    def _play_section(self, rhythm, num_measures, part_filter=None):
        """Internal helper to play a section of music and block for its duration."""
        seconds_per_beat = 60.0 / rhythm['bpm']
        measure_duration = rhythm['beats_per_measure'] * seconds_per_beat
        total_duration = num_measures * measure_duration
        
        section_start_time = time.monotonic()
        parts_to_play = rhythm['parts'].items()
        if part_filter:
            parts_to_play = [(k, v) for k, v in parts_to_play if part_filter(k)]

        for i in range(num_measures):
            if self.stop_event.is_set(): return
            measure_start_time = section_start_time + (i * measure_duration)
            for _, part_notes in parts_to_play:
                for beat, note, velocity, duration in part_notes:
                    note_on_time = measure_start_time + (beat * seconds_per_beat)
                    note_off_time = note_on_time + (duration * seconds_per_beat)
                    self.scheduler.schedule_event(note_on_time, [0x90 | DRUM_CHANNEL, note, velocity])
                    self.scheduler.schedule_event(note_off_time, [0x80 | DRUM_CHANNEL, note, 0])
        
        # Block for the duration of the scheduled section
        time_to_wait = total_duration - (time.monotonic() - section_start_time)
        if time_to_wait > 0:
            self.stop_event.wait(time_to_wait)


    def run(self):
        current_rhythm = self.rhythm1
        print(f"\n---> Starting mix with {current_rhythm['name']}...")

        while not self.stop_event.is_set():
            action = random.choices(['play_full', 'breakdown', 'swap'], weights=[0.5, 0.2, 0.3], k=1)[0]
            
            if action == 'play_full':
                self._play_section(current_rhythm, num_measures=4)

            elif action == 'breakdown':
                print("... Breakdown ...")
                # Define core parts for breakdown
                core_parts = lambda part: "bell" in part.lower() or "shaker" in part.lower() or "gankogui" in part.lower()
                self._play_section(current_rhythm, num_measures=2, part_filter=core_parts)
                
                print("... Buildup ...")
                all_parts = list(current_rhythm['parts'].keys())
                for i in range(1, len(all_parts) + 1):
                    parts_to_include = all_parts[:i]
                    build_filter = lambda part: part in parts_to_include
                    self._play_section(current_rhythm, num_measures=1, part_filter=build_filter)
            
            elif action == 'swap':
                self._play_section(current_rhythm, num_measures=3)
                print("... Fill and Swap ...")
                # Play a 4/4 fill before swapping
                fill_pattern = random.choice(DRUM_FILLS)
                fill_rhythm = {"bpm": current_rhythm['bpm'], "beats_per_measure": 4, "parts": {"fill": fill_pattern}}
                self._play_section(fill_rhythm, num_measures=1)

                current_rhythm = self.rhythm2 if current_rhythm == self.rhythm1 else self.rhythm1
                print(f"---> Swapped to {current_rhythm['name']} <---")
                # Play a measure of the new rhythm to establish it
                self._play_section(current_rhythm, num_measures=2)

    def stop(self):
        self.stop_event.set()

# ================================== Main Application ==================================

def display_menu():
    print("\n" + "="*50)
    print("      AFRICAN RHYTHM MIDI PLAYER")
    print("="*50)
    for key, val in AFRICAN_RHYTHMS.items():
        print(f"  [{key}] {val['name']} ({val['bpm']} BPM)")
    print(f"  [4] Dynamic Mix ({AFRICAN_RHYTHMS['1']['name']} & {AFRICAN_RHYTHMS['2']['name']})")
    print("\n  [r] Return to this menu / Stop playback")
    print("  [q] Quit")
    print("-"*50)

def silence_all_notes(midiout):
    for ch in range(16):
        midiout.send_message([0xB0 | ch, 123, 0])
    print("All notes silenced.")

def main():
    midiout = rtmidi.MidiOut()
    try:
        midiout.open_port(PORT_INDEX)
        print(f"MIDI Port '{midiout.get_ports()[PORT_INDEX]}' opened.")
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
                
                if active_player:
                    print("Stopping current rhythm...")
                    active_player.stop()
                    active_player.join()
                    active_player = None
                    silence_all_notes(midiout)
                
                if key == 'r':
                    display_menu()
                    continue

                if key in AFRICAN_RHYTHMS:
                    rhythm_data = AFRICAN_RHYTHMS[key]
                    print(f"Playing '{rhythm_data['name']}'... (Press 'r' to stop)")
                    active_player = RhythmPlayer(scheduler, rhythm_data)
                    active_player.start()
                
                elif key == '4':
                    print("Starting Dynamic Mix... (Press 'r' to stop)")
                    r1 = AFRICAN_RHYTHMS['1']
                    r2 = AFRICAN_RHYTHMS['2']
                    active_player = DynamicMixPlayer(scheduler, r1, r2)
                    active_player.start()

            time.sleep(0.01)

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