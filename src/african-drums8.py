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

PORT_INDEX = 0
VEL_ACCENT = 120
VEL_NORMAL = 100
VEL_GHOST = 70
DRUM_CHANNEL = 9  # MIDI channel 10 (0-indexed)
MELODY_CHANNEL = 0 # MIDI channel 1 (0-indexed)
MELODY_INSTRUMENT = 108 # GM Program #109: Kalimba

# ================================== RHYTHM & FILL DEFINITIONS ==================================
# Each rhythm: (beat, midi_note, velocity, duration_in_beats)
AFRICAN_RHYTHMS = {
    "1": {
        "name": "Fanga (Liberia/Guinea)", "bpm": 130, "beats_per_measure": 4,
        "parts": {
            "Dundun": [(0, 45, VEL_ACCENT, 0.5), (2, 45, VEL_ACCENT, 0.5)], "Sangban": [(1, 47, VEL_NORMAL, 0.25), (3, 47, VEL_NORMAL, 0.25)],
            "Kenkeni (Bell)": [(0, 56, VEL_NORMAL, 0.1), (0.5, 56, VEL_GHOST, 0.1), (1, 56, VEL_NORMAL, 0.1), (1.5, 56, VEL_GHOST, 0.1), (2, 56, VEL_NORMAL, 0.1), (2.5, 56, VEL_GHOST, 0.1), (3, 56, VEL_NORMAL, 0.1), (3.5, 56, VEL_GHOST, 0.1)],
            "Djembe": [(0.75, 60, VEL_NORMAL, 0.1), (1.5, 63, VEL_ACCENT, 0.1), (2.75, 60, VEL_NORMAL, 0.1), (3.25, 63, VEL_NORMAL, 0.1), (3.75, 63, VEL_ACCENT, 0.1)]
        }
    },
    "2": {
        "name": "Agbekor (Ewe - Ghana)", "bpm": 110, "beats_per_measure": 12,
        "parts": {
            "Gankogui (Bell)": [(0, 67, VEL_ACCENT, 0.5), (2, 68, VEL_NORMAL, 0.5), (3, 67, VEL_ACCENT, 0.5), (5, 68, VEL_NORMAL, 0.5), (6, 67, VEL_ACCENT, 0.5), (7, 68, VEL_NORMAL, 0.5), (9, 68, VEL_NORMAL, 0.5), (10, 67, VEL_ACCENT, 0.5)],
            "Axatse (Shaker)": [(0, 70, VEL_NORMAL, 0.2), (3, 70, VEL_NORMAL, 0.2), (6, 70, VEL_NORMAL, 0.2), (9, 70, VEL_NORMAL, 0.2)],
            "Kagan (Drum)": [(1, 62, VEL_NORMAL, 0.2), (2, 62, VEL_GHOST, 0.2), (4, 62, VEL_NORMAL, 0.2), (5, 62, VEL_GHOST, 0.2), (7, 62, VEL_NORMAL, 0.2), (8, 62, VEL_GHOST, 0.2), (10, 62, VEL_NORMAL, 0.2), (11, 62, VEL_GHOST, 0.2)]
        }
    },
    "3": {
        "name": "Kpanlogo (Ga - Ghana)", "bpm": 125, "beats_per_measure": 4,
        "parts": {
            "Bell": [(0, 56, VEL_ACCENT, 0.2), (1, 56, VEL_NORMAL, 0.2), (1.5, 56, VEL_NORMAL, 0.2), (2.5, 56, VEL_ACCENT, 0.2), (3, 56, VEL_NORMAL, 0.2)],
            "Conga 1": [(0, 62, VEL_ACCENT, 0.2), (2, 62, VEL_ACCENT, 0.2), (3.5, 62, VEL_ACCENT, 0.2)], "Conga 2": [(1, 65, VEL_NORMAL, 0.2), (1.5, 62, VEL_GHOST, 0.2), (3, 65, VEL_NORMAL, 0.2)]
        }
    },
    "4": {
        "name": "Bikutsi (Cameroon)", "bpm": 140, "beats_per_measure": 6,
        "parts": {
            "Kick": [(0, 36, VEL_ACCENT, 0.2), (3, 36, VEL_ACCENT, 0.2)], "Snare": [(1.5, 38, VEL_NORMAL, 0.2), (4.5, 38, VEL_NORMAL, 0.2)],
            "Woodblock": [(0, 76, VEL_NORMAL, 0.1), (1, 76, VEL_GHOST, 0.1), (2, 76, VEL_NORMAL, 0.1), (3, 76, VEL_NORMAL, 0.1), (4, 76, VEL_GHOST, 0.1), (5, 76, VEL_NORMAL, 0.1)],
        }
    },
    "5": {
        "name": "Shiko (Nigeria)", "bpm": 115, "beats_per_measure": 4,
        "parts": {
            "Bell": [(0, 56, VEL_ACCENT, 0.2), (0.75, 56, VEL_NORMAL, 0.2), (1.5, 56, VEL_NORMAL, 0.2), (2.5, 56, VEL_ACCENT, 0.2), (3.25, 56, VEL_NORMAL, 0.2)],
            "Low Tom": [(0, 45, VEL_ACCENT, 0.2), (2, 45, VEL_GHOST, 0.2)], "High Tom": [(1, 50, VEL_NORMAL, 0.2), (3, 50, VEL_NORMAL, 0.2), (3.5, 50, VEL_ACCENT, 0.2)],
        }
    },
    "6": {
        "name": "Wassoulou (Mali)", "bpm": 128, "beats_per_measure": 4,
        "parts": {
            "Djembe Bass": [(0, 60, VEL_ACCENT, 0.2), (2, 60, VEL_ACCENT, 0.2)],
            "Djembe Tone": [(1, 63, VEL_NORMAL, 0.2), (2.5, 63, VEL_ACCENT, 0.2), (3, 63, VEL_NORMAL, 0.2), (3.5, 63, VEL_GHOST, 0.2)],
            "Kenkeni (Bell)": [(0, 56, VEL_NORMAL, 0.1), (1, 56, VEL_GHOST, 0.1), (2, 56, VEL_NORMAL, 0.1), (3, 56, VEL_GHOST, 0.1)],
        }
    },
    "7": {
        "name": "Moribayassa (Guinea)", "bpm": 150, "beats_per_measure": 4,
        "parts": {
            "Djembe Slap": [(0.75, 62, VEL_ACCENT, 0.15), (1.75, 62, VEL_ACCENT, 0.15), (2.75, 62, VEL_ACCENT, 0.15), (3.75, 62, VEL_ACCENT, 0.15)],
            "Djembe Tone": [(0.5, 63, VEL_NORMAL, 0.1), (1.5, 63, VEL_NORMAL, 0.1), (2.5, 63, VEL_NORMAL, 0.1), (3.5, 63, VEL_NORMAL, 0.1)],
            "Dundun": [(0, 45, VEL_ACCENT, 0.2), (1, 45, VEL_NORMAL, 0.2), (2, 45, VEL_ACCENT, 0.2), (3, 45, VEL_NORMAL, 0.2)],
        }
    }
}
DRUM_FILLS = [
    [(0.0,48,VEL_NORMAL,0.2),(0.5,47,VEL_NORMAL,0.2),(1.0,45,VEL_NORMAL,0.2),(1.5,43,VEL_NORMAL,0.2),(2.0,50,VEL_ACCENT,0.2),(2.5,48,VEL_NORMAL,0.2),(3.0,47,VEL_ACCENT,0.2),(3.5,45,VEL_ACCENT,0.5)],
    [(0.0,38,VEL_NORMAL,0.2),(0.75,63,VEL_GHOST,0.2),(1.5,38,VEL_ACCENT,0.2),(2.0,64,VEL_NORMAL,0.2),(2.5,38,VEL_NORMAL,0.2),(3.25,63,VEL_ACCENT,0.2)],
    [(0.0,64,VEL_NORMAL,0.25),(0.25,63,VEL_NORMAL,0.25),(0.5,62,VEL_NORMAL,0.25),(0.75,61,VEL_NORMAL,0.25),(1.0,48,VEL_ACCENT,0.2),(1.5,47,VEL_ACCENT,0.2),(2.0,45,VEL_ACCENT,0.2),(2.5,43,VEL_ACCENT,1.5)]
]
# A minor pentatonic scale (A, C, D, E, G), a common scale in African music
MELODY_SCALE = [69, 72, 74, 76, 79, 81] # A4, C5, D5, E5, G5, A5
MELODY_RHYTHMS = [[0.5, 1.5, 2.5], [0, 1, 2, 3], [0.75, 2.25, 3.5]]

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

class RhythmicMixPlayer(threading.Thread):
    """A player that mixes rhythms with musically-aware progressions."""
    STATE_GROOVE, STATE_BREAKDOWN, STATE_BUILDUP, STATE_FILL_SWAP = range(4)

    def __init__(self, scheduler, rhythm1_data, rhythm2_data):
        super().__init__(daemon=True)
        self.scheduler = scheduler
        self.rhythms = [rhythm1_data, rhythm2_data]
        self.current_rhythm_idx = 0
        self.stop_event = threading.Event()
        self.state = self.STATE_GROOVE
        self.measures_in_state = 0

    def _play_section(self, rhythm, num_measures, part_filter=None):
        if self.stop_event.is_set(): return
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
        
        time_to_wait = total_duration - (time.monotonic() - section_start_time)
        if time_to_wait > 0:
            self.stop_event.wait(time_to_wait)

    def run(self):
        current_rhythm = self.rhythms[self.current_rhythm_idx]
        print(f"\n---> Starting mix with {current_rhythm['name']}...")

        while not self.stop_event.is_set():
            current_rhythm = self.rhythms[self.current_rhythm_idx]

            if self.state == self.STATE_GROOVE:
                play_measures = random.randint(4, 8)
                self._play_section(current_rhythm, num_measures=play_measures)
                if random.random() < 0.7: self.state = self.STATE_BREAKDOWN
                
            elif self.state == self.STATE_BREAKDOWN:
                print("... Breakdown ...")
                core_parts = lambda part: "bell" in part.lower() or "shaker" in part.lower() or "gankogui" in part.lower()
                self._play_section(current_rhythm, num_measures=2, part_filter=core_parts)
                self.state = self.STATE_BUILDUP

            elif self.state == self.STATE_BUILDUP:
                print("... Buildup ...")
                all_parts = list(current_rhythm['parts'].keys())
                random.shuffle(all_parts)
                parts_to_include = [p for p in all_parts if "bell" in p.lower() or "shaker" in p.lower() or "gankogui" in p.lower()]
                for part in all_parts:
                    if part not in parts_to_include:
                        parts_to_include.append(part)
                        build_filter = lambda p_name: p_name in parts_to_include
                        self._play_section(current_rhythm, num_measures=1, part_filter=build_filter)
                self.state = self.STATE_FILL_SWAP

            elif self.state == self.STATE_FILL_SWAP:
                print("... Fill and Swap ...")
                fill_pattern = random.choice(DRUM_FILLS)
                fill_rhythm = {"bpm": current_rhythm['bpm'], "beats_per_measure": 4, "parts": {"fill": fill_pattern}}
                self._play_section(fill_rhythm, num_measures=1)
                
                self.current_rhythm_idx = 1 - self.current_rhythm_idx
                next_rhythm = self.rhythms[self.current_rhythm_idx]
                print(f"---> Swapped to {next_rhythm['name']} <---")
                self.state = self.STATE_GROOVE

    def stop(self):
        self.stop_event.set()

class MelodicMixPlayer(RhythmicMixPlayer):
    """Extends the RhythmicMixPlayer to add a generated melody."""
    def __init__(self, scheduler, rhythm1_data, rhythm2_data):
        super().__init__(scheduler, rhythm1_data, rhythm2_data)
        self.melody_thread = threading.Thread(target=self._melody_loop, daemon=True)
        # Set the melody instrument
        scheduler.midiout.send_message([0xC0 | MELODY_CHANNEL, MELODY_INSTRUMENT])
        print(f"Melody instrument set to Kalimba on channel {MELODY_CHANNEL + 1}.")

    def _melody_loop(self):
        """A separate loop for generating and scheduling melody notes."""
        last_note = random.choice(MELODY_SCALE)
        while not self.stop_event.is_set():
            current_rhythm = self.rhythms[self.current_rhythm_idx]
            seconds_per_beat = 60.0 / current_rhythm['bpm']
            measure_duration = current_rhythm['beats_per_measure'] * seconds_per_beat
            measure_start_time = time.monotonic()
            
            if self.state == self.STATE_GROOVE:
                # Generate melody for one measure
                rhythmic_motif = random.choice(MELODY_RHYTHMS)
                for beat in rhythmic_motif:
                    note_on_time = measure_start_time + (beat * seconds_per_beat)
                    note_off_time = note_on_time + (0.5 * seconds_per_beat) # Half a beat duration
                    
                    # Choose a note, making it more likely to be near the last note
                    note = random.choices(
                        MELODY_SCALE, 
                        weights=[(10 - abs(n - last_note)) for n in MELODY_SCALE], 
                        k=1
                    )[0]
                    last_note = note
                    velocity = random.randint(70, 110)
                    
                    self.scheduler.schedule_event(note_on_time, [0x90 | MELODY_CHANNEL, note, velocity])
                    self.scheduler.schedule_event(note_off_time, [0x80 | MELODY_CHANNEL, note, 0])

            self.stop_event.wait(measure_duration)

    def run(self):
        self.melody_thread.start()
        super().run() # Start the main rhythm loop

    def stop(self):
        super().stop()
        if self.melody_thread.is_alive():
            self.melody_thread.join()

# ================================== Main Application ==================================
def display_menu():
    print("\n" + "="*60)
    print("                AFRICAN RHYTHM MIDI PLAYER")
    print("="*60)
    for i in range(1, 8):
        key = str(i)
        if key in AFRICAN_RHYTHMS:
            val = AFRICAN_RHYTHMS[key]
            print(f"  [{key}] {val['name']:<25} ({val['bpm']} BPM, {val['beats_per_measure']}/8)")
    print("-" * 60)
    r_mix = f"Rhythmic Mix ({AFRICAN_RHYTHMS['1']['name']} & {AFRICAN_RHYTHMS['3']['name']})"
    m_mix = f"Melodic Mix  ({AFRICAN_RHYTHMS['1']['name']} & {AFRICAN_RHYTHMS['3']['name']})"
    print(f"  [8] {r_mix}")
    print(f"  [9] {m_mix}")
    print("\n  [r] Return to this menu / Stop playback")
    print("  [q] Quit")
    print("-"*60)

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
                
                elif key == '8':
                    print("Starting Rhythmic Mix... (Press 'r' to stop)")
                    r1 = AFRICAN_RHYTHMS['1']
                    r3 = AFRICAN_RHYTHMS['3']
                    active_player = RhythmicMixPlayer(scheduler, r1, r3)
                    active_player.start()
                
                elif key == '9':
                    print("Starting Melodic Mix... (Press 'r' to stop)")
                    r1 = AFRICAN_RHYTHMS['1']
                    r3 = AFRICAN_RHYTHMS['3']
                    active_player = MelodicMixPlayer(scheduler, r1, r3)
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