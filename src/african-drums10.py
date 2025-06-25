
# AI The melody is too random. Match some african style melodies to the rhythms
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
        "build_order": ['Kenkeni (Bell)', 'Sangban', 'Dundun', 'Djembe'],
        "parts": {
            "Dundun": [(0, 45, VEL_ACCENT, 0.5), (2, 45, VEL_ACCENT, 0.5)], "Sangban": [(1, 47, VEL_NORMAL, 0.25), (3, 47, VEL_NORMAL, 0.25)],
            "Kenkeni (Bell)": [(0, 56, VEL_NORMAL, 0.1), (0.5, 56, VEL_GHOST, 0.1), (1, 56, VEL_NORMAL, 0.1), (1.5, 56, VEL_GHOST, 0.1), (2, 56, VEL_NORMAL, 0.1), (2.5, 56, VEL_GHOST, 0.1), (3, 56, VEL_NORMAL, 0.1), (3.5, 56, VEL_GHOST, 0.1)],
            "Djembe": [(0.75, 60, VEL_NORMAL, 0.1), (1.5, 63, VEL_ACCENT, 0.1), (2.75, 60, VEL_NORMAL, 0.1), (3.25, 63, VEL_NORMAL, 0.1), (3.75, 63, VEL_ACCENT, 0.1)]
        }
    },
    "2": {
        "name": "Agbekor (Ewe - Ghana)", "bpm": 110, "beats_per_measure": 12,
        "build_order": ['Gankogui (Bell)', 'Axatse (Shaker)', 'Kagan (Drum)'],
        "parts": {
            "Gankogui (Bell)": [(0, 67, VEL_ACCENT, 0.5), (2, 68, VEL_NORMAL, 0.5), (3, 67, VEL_ACCENT, 0.5), (5, 68, VEL_NORMAL, 0.5), (6, 67, VEL_ACCENT, 0.5), (7, 68, VEL_NORMAL, 0.5), (9, 68, VEL_NORMAL, 0.5), (10, 67, VEL_ACCENT, 0.5)],
            "Axatse (Shaker)": [(0, 70, VEL_NORMAL, 0.2), (3, 70, VEL_NORMAL, 0.2), (6, 70, VEL_NORMAL, 0.2), (9, 70, VEL_NORMAL, 0.2)],
            "Kagan (Drum)": [(1, 62, VEL_NORMAL, 0.2), (2, 62, VEL_GHOST, 0.2), (4, 62, VEL_NORMAL, 0.2), (5, 62, VEL_GHOST, 0.2), (7, 62, VEL_NORMAL, 0.2), (8, 62, VEL_GHOST, 0.2), (10, 62, VEL_NORMAL, 0.2), (11, 62, VEL_GHOST, 0.2)]
        }
    },
    "3": {
        "name": "Kpanlogo (Ga - Ghana)", "bpm": 125, "beats_per_measure": 4,
        "build_order": ['Bell', 'Conga 2', 'Conga 1'],
        "parts": {
            "Bell": [(0, 56, VEL_ACCENT, 0.2), (1, 56, VEL_NORMAL, 0.2), (1.5, 56, VEL_NORMAL, 0.2), (2.5, 56, VEL_ACCENT, 0.2), (3, 56, VEL_NORMAL, 0.2)],
            "Conga 1": [(0, 62, VEL_ACCENT, 0.2), (2, 62, VEL_ACCENT, 0.2), (3.5, 62, VEL_ACCENT, 0.2)], "Conga 2": [(1, 65, VEL_NORMAL, 0.2), (1.5, 62, VEL_GHOST, 0.2), (3, 65, VEL_NORMAL, 0.2)]
        }
    },
    "4": {
        "name": "Bikutsi (Cameroon)", "bpm": 140, "beats_per_measure": 6,
        "build_order": ['Woodblock', 'Snare', 'Kick'],
        "parts": { "Kick": [(0, 36, VEL_ACCENT, 0.2), (3, 36, VEL_ACCENT, 0.2)], "Snare": [(1.5, 38, VEL_NORMAL, 0.2), (4.5, 38, VEL_NORMAL, 0.2)], "Woodblock": [(0, 76, VEL_NORMAL, 0.1), (1, 76, VEL_GHOST, 0.1), (2, 76, VEL_NORMAL, 0.1), (3, 76, VEL_NORMAL, 0.1), (4, 76, VEL_GHOST, 0.1), (5, 76, VEL_NORMAL, 0.1)] }
    },
    "5": {
        "name": "Shiko (Nigeria)", "bpm": 115, "beats_per_measure": 4,
        "build_order": ['Bell', 'Low Tom', 'High Tom'],
        "parts": { "Bell": [(0, 56, VEL_ACCENT, 0.2), (0.75, 56, VEL_NORMAL, 0.2), (1.5, 56, VEL_NORMAL, 0.2), (2.5, 56, VEL_ACCENT, 0.2), (3.25, 56, VEL_NORMAL, 0.2)], "Low Tom": [(0, 45, VEL_ACCENT, 0.2), (2, 45, VEL_GHOST, 0.2)], "High Tom": [(1, 50, VEL_NORMAL, 0.2), (3, 50, VEL_NORMAL, 0.2), (3.5, 50, VEL_ACCENT, 0.2)] }
    },
    "6": {
        "name": "Wassoulou (Mali)", "bpm": 128, "beats_per_measure": 4,
        "build_order": ['Kenkeni (Bell)', 'Djembe Tone', 'Djembe Bass'],
        "parts": { "Djembe Bass": [(0, 60, VEL_ACCENT, 0.2), (2, 60, VEL_ACCENT, 0.2)], "Djembe Tone": [(1, 63, VEL_NORMAL, 0.2), (2.5, 63, VEL_ACCENT, 0.2), (3, 63, VEL_NORMAL, 0.2), (3.5, 63, VEL_GHOST, 0.2)], "Kenkeni (Bell)": [(0, 56, VEL_NORMAL, 0.1), (1, 56, VEL_GHOST, 0.1), (2, 56, VEL_NORMAL, 0.1), (3, 56, VEL_GHOST, 0.1)] }
    },
    "7": {
        "name": "Moribayassa (Guinea)", "bpm": 150, "beats_per_measure": 4,
        "build_order": ['Dundun', 'Djembe Tone', 'Djembe Slap'],
        "parts": { "Djembe Slap": [(0.75, 62, VEL_ACCENT, 0.15), (1.75, 62, VEL_ACCENT, 0.15), (2.75, 62, VEL_ACCENT, 0.15), (3.75, 62, VEL_ACCENT, 0.15)], "Djembe Tone": [(0.5, 63, VEL_NORMAL, 0.1), (1.5, 63, VEL_NORMAL, 0.1), (2.5, 63, VEL_NORMAL, 0.1), (3.5, 63, VEL_NORMAL, 0.1)], "Dundun": [(0, 45, VEL_ACCENT, 0.2), (1, 45, VEL_NORMAL, 0.2), (2, 45, VEL_ACCENT, 0.2), (3, 45, VEL_NORMAL, 0.2)] }
    }
}
DRUM_FILLS = [
    [(0.0,48,VEL_NORMAL,0.2),(0.5,47,VEL_NORMAL,0.2),(1.0,45,VEL_NORMAL,0.2),(1.5,43,VEL_NORMAL,0.2),(2.0,50,VEL_ACCENT,0.2),(2.5,48,VEL_NORMAL,0.2),(3.0,47,VEL_ACCENT,0.2),(3.5,45,VEL_ACCENT,0.5)],
    [(0.0,38,VEL_NORMAL,0.2),(0.75,63,VEL_GHOST,0.2),(1.5,38,VEL_ACCENT,0.2),(2.0,64,VEL_NORMAL,0.2),(2.5,38,VEL_NORMAL,0.2),(3.25,63,VEL_ACCENT,0.2)],
    [(0.0,64,VEL_NORMAL,0.25),(0.25,63,VEL_NORMAL,0.25),(0.5,62,VEL_NORMAL,0.25),(0.75,61,VEL_NORMAL,0.25),(1.0,48,VEL_ACCENT,0.2),(1.5,47,VEL_ACCENT,0.2),(2.0,45,VEL_ACCENT,0.2),(2.5,43,VEL_ACCENT,1.5)]
]

# ================================== MELODY GENERATION DATA ==================================
MELODY_SCALE = [69, 72, 74, 76, 79, 81, 84] # A minor pentatonic (A4, C5, D5, E5, G5, A5, C6)

# Phrases are defined as lists of (beat, scale_degree) tuples.
MELODIC_PHRASES = {
    'Fanga (Liberia/Guinea)': {
        'calls': [
            [(0.5, 2), (1.5, 4), (2.5, 3)],              # Upward arc
            [(0.75, 4), (2.25, 2), (3.25, 1)]            # Syncopated descent
        ],
        'responses': [
            [(0.5, 1), (1.5, 0), (2.5, -1)],             # Answering descent (relative to scale)
            [(0.75, 2), (1.75, 1), (3.25, 0)],           # Syncopated answer
            [(0.5, 4), (1.0, 5), (1.5, 4), (3.0, 3)]    # More complex response
        ]
    },
    'Kpanlogo (Ga - Ghana)': {
        'calls': [
            [(0, 0), (0.75, 2), (1.5, 4)],              # Driving, ascending
            [(0.5, 4), (1.5, 3), (2.5, 2)]              # On-beat descent
        ],
        'responses': [
            [(0.75, 3), (1.75, 2), (2.75, 1), (3.75, 0)],# 16th note feel answer
            [(0.5, 1), (1.5, 0), (3.0, 2), (3.5, 1)]     # Syncopated response
        ]
    }
}

# ================================== High-Precision MIDI Scheduler ==================================
class MidiScheduler(threading.Thread):
    def __init__(self, midiout):
        super().__init__(daemon=True)
        self.midiout = midiout; self.events = []; self.lock = threading.Lock(); self.running = threading.Event(); self.running.set()
    def schedule_event(self, play_time, msg):
        with self.lock: self.events.append((play_time, msg)); self.events.sort()
    def run(self):
        while self.running.is_set():
            now = time.monotonic()
            with self.lock:
                if not self.events: sleep_time = 0.005
                else:
                    next_event_time = self.events[0][0]
                    if next_event_time <= now: _, msg = self.events.pop(0); self.midiout.send_message(msg); continue
                    else: sleep_time = next_event_time - now
            time.sleep(max(0, sleep_time))
    def stop(self): self.running.clear()

# ================================== Rhythm Player Threads ==================================
class RhythmPlayer(threading.Thread):
    def __init__(self, scheduler, rhythm_data):
        super().__init__(daemon=True)
        self.scheduler = scheduler; self.rhythm = rhythm_data; self.stop_event = threading.Event()
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
            if sleep_duration > 0: self.stop_event.wait(sleep_duration)
    def stop(self): self.stop_event.set()

class RhythmicMixPlayer(threading.Thread):
    STATE_GROOVE, STATE_DECONSTRUCT, STATE_BREAKDOWN, STATE_BUILDUP, STATE_FILL_SWAP = range(5)
    def __init__(self, scheduler, rhythm1_data, rhythm2_data):
        super().__init__(daemon=True)
        self.scheduler = scheduler; self.rhythms = [rhythm1_data, rhythm2_data]
        self.current_rhythm_idx = 0; self.stop_event = threading.Event()
        self.state = self.STATE_GROOVE
    def _play_section(self, rhythm, num_measures, part_filter=None, custom_parts=None):
        if self.stop_event.is_set(): return
        seconds_per_beat = 60.0 / rhythm['bpm']
        measure_duration = rhythm['beats_per_measure'] * seconds_per_beat
        total_duration = num_measures * measure_duration
        section_start_time = time.monotonic()
        parts_to_play = custom_parts if custom_parts is not None else rhythm['parts'].items()
        if part_filter: parts_to_play = [(k, v) for k, v in parts_to_play if part_filter(k)]
        for i in range(num_measures):
            if self.stop_event.is_set(): return
            measure_start_time = section_start_time + (i * measure_duration)
            for _, part_notes in parts_to_play:
                for beat, note, velocity, duration, channel in part_notes:
                    note_on_time = measure_start_time + (beat * seconds_per_beat)
                    note_off_time = note_on_time + (duration * seconds_per_beat)
                    self.scheduler.schedule_event(note_on_time, [0x90 | channel, note, velocity])
                    self.scheduler.schedule_event(note_off_time, [0x80 | channel, note, 0])
        time_to_wait = total_duration - (time.monotonic() - section_start_time)
        if time_to_wait > 0: self.stop_event.wait(time_to_wait)
    
    def _handle_groove(self, current_rhythm, parts_with_channel):
        play_measures = random.randint(4, 6)
        self._play_section(current_rhythm, num_measures=play_measures, custom_parts=parts_with_channel.items())
        if random.random() < 0.8: self.state = self.STATE_DECONSTRUCT

    def _handle_deconstruct(self, current_rhythm, parts_with_channel):
        print("... Deconstructing ...")
        core_parts = [p for p in current_rhythm['build_order'] if "bell" in p.lower() or "shaker" in p.lower()]
        parts_to_remove = [p for p in current_rhythm['build_order'] if p not in core_parts]
        parts_to_remove.reverse()
        active_parts = list(current_rhythm['build_order'])
        for part_to_remove in parts_to_remove:
            if self.stop_event.is_set(): return
            build_filter = lambda p_name: p_name in active_parts
            self._play_section(current_rhythm, 1, part_filter=build_filter, custom_parts=parts_with_channel.items())
            active_parts.remove(part_to_remove)
        self.state = self.STATE_BREAKDOWN

    def _handle_breakdown(self, current_rhythm, parts_with_channel):
        print("... Breakdown ...")
        core_parts_filter = lambda p: "bell" in p.lower() or "shaker" in p.lower()
        self._play_section(current_rhythm, num_measures=2, part_filter=core_parts_filter, custom_parts=parts_with_channel.items())
        self.state = self.STATE_BUILDUP
            
    def _handle_buildup(self, current_rhythm, parts_with_channel):
        print("... Buildup ...")
        build_order = list(current_rhythm['build_order'])
        core_parts = [p for p in build_order if "bell" in p.lower() or "shaker" in p.lower()]
        parts_to_add = [p for p in build_order if p not in core_parts]
        active_parts = core_parts[:]
        for part_to_add in parts_to_add:
            if self.stop_event.is_set(): return
            build_filter = lambda p_name: p_name in active_parts
            self._play_section(current_rhythm, 1, part_filter=build_filter, custom_parts=parts_with_channel.items())
            active_parts.append(part_to_add)
        self.state = self.STATE_FILL_SWAP
            
    def _handle_fill_swap(self, current_rhythm):
        print("... Fill and Swap ...")
        fill_pattern = random.choice(DRUM_FILLS)
        fill_with_channel = [(n[0], n[1], n[2], n[3], DRUM_CHANNEL) for n in fill_pattern]
        fill_rhythm = {"bpm": current_rhythm['bpm'], "beats_per_measure": 4, "parts": {"fill": fill_with_channel}}
        self._play_section(fill_rhythm, num_measures=1)
        self.current_rhythm_idx = 1 - self.current_rhythm_idx
        next_rhythm = self.rhythms[self.current_rhythm_idx]
        print(f"---> Swapped to {next_rhythm['name']} <---"); self.state = self.STATE_GROOVE

    def run(self):
        current_rhythm = self.rhythms[self.current_rhythm_idx]
        print(f"\n---> Starting mix with {current_rhythm['name']}...")
        while not self.stop_event.is_set():
            current_rhythm = self.rhythms[self.current_rhythm_idx]
            parts_with_channel = {name: [(n[0], n[1], n[2], n[3], DRUM_CHANNEL) for n in notes] for name, notes in current_rhythm['parts'].items()}
            
            if self.state == self.STATE_GROOVE:
                self._handle_groove(current_rhythm, parts_with_channel)
            elif self.state == self.STATE_DECONSTRUCT:
                self._handle_deconstruct(current_rhythm, parts_with_channel)
            elif self.state == self.STATE_BREAKDOWN:
                self._handle_breakdown(current_rhythm, parts_with_channel)
            elif self.state == self.STATE_BUILDUP:
                self._handle_buildup(current_rhythm, parts_with_channel)
            elif self.state == self.STATE_FILL_SWAP:
                self._handle_fill_swap(current_rhythm)
    def stop(self): self.stop_event.set()

class MelodicMixPlayer(RhythmicMixPlayer):
    def __init__(self, scheduler, rhythm1_data, rhythm2_data):
        super().__init__(scheduler, rhythm1_data, rhythm2_data)
        scheduler.midiout.send_message([0xC0 | MELODY_CHANNEL, MELODY_INSTRUMENT])
        print(f"Melody instrument set to Kalimba on channel {MELODY_CHANNEL + 1}.")
        self.last_note_idx = len(MELODY_SCALE) // 2
        self.is_call = True

    def _generate_melodic_phrase(self, rhythm_name, base_note_idx):
        """Generates a melodic phrase using a call-and-response structure."""
        phrase_lib = MELODIC_PHRASES[rhythm_name]
        
        if self.is_call:
            phrase_pattern = random.choice(phrase_lib['calls'])
        else:
            phrase_pattern = random.choice(phrase_lib['responses'])
        
        # Alternate for next time
        self.is_call = not self.is_call

        phrase = []
        for beat, degree in phrase_pattern:
            # Ensure the note stays within the defined scale
            note_idx = max(0, min(len(MELODY_SCALE) - 1, base_note_idx + degree))
            note = MELODY_SCALE[note_idx]
            duration = 0.4
            velocity = random.randint(80, 110)
            phrase.append((beat, note, velocity, duration, MELODY_CHANNEL))
            
        return phrase, base_note_idx # Return the original base index for phrase consistency

    def _handle_groove(self, current_rhythm, parts_with_channel):
        """Override to inject melody generation into the groove state."""
        play_measures = random.randint(2, 3) * 2 # Play in pairs for call/response
        
        for i in range(play_measures):
            if self.stop_event.is_set(): break
            
            # Generate one measure of melody
            phrase, self.last_note_idx = self._generate_melodic_phrase(current_rhythm['name'], self.last_note_idx)
            
            # Combine with rhythmic parts for this measure
            all_parts = parts_with_channel.copy()
            all_parts['melody'] = phrase
            self._play_section(current_rhythm, num_measures=1, custom_parts=all_parts.items())
        
        # Transition to the next state
        if random.random() < 0.7:
            self.state = self.STATE_DECONSTRUCT
    
    def run(self):
        # Override the main run loop to insert the print statement at the right time
        print(f"\n---> Starting Melodic Mix with {self.rhythms[0]['name']}...")
        super().run() # Now call the parent's run method which contains the state machine

# ================================== Main Application ==================================
def display_menu():
    print("\n" + "="*60); print("                AFRICAN RHYTHM MIDI PLAYER"); print("="*60)
    for i in range(1, 8):
        key = str(i)
        if key in AFRICAN_RHYTHMS: val = AFRICAN_RHYTHMS[key]; print(f"  [{key}] {val['name']:<25} ({val['bpm']} BPM, {val['beats_per_measure']}/8)")
    print("-" * 60)
    r_mix = f"Rhythmic Mix ({AFRICAN_RHYTHMS['1']['name']} & {AFRICAN_RHYTHMS['3']['name']})"
    m_mix = f"Melodic Mix  ({AFRICAN_RHYTHMS['1']['name']} & {AFRICAN_RHYTHMS['3']['name']})"
    print(f"  [8] {r_mix}"); print(f"  [9] {m_mix}")
    print("\n  [r] Return to this menu / Stop playback"); print("  [q] Quit"); print("-"*60)
def silence_all_notes(midiout):
    for ch in range(16): midiout.send_message([0xB0 | ch, 123, 0])
    print("All notes silenced.")
def main():
    midiout = rtmidi.MidiOut()
    try: midiout.open_port(PORT_INDEX); print(f"MIDI Port '{midiout.get_ports()[PORT_INDEX]}' opened.")
    except (rtmidi.InvalidPortError, rtmidi.NoPortsAvailableError): print(f"Error: MIDI Port {PORT_INDEX} not available."); print("Available ports:", midiout.get_ports()); return
    scheduler = MidiScheduler(midiout); scheduler.start(); active_player = None
    try:
        display_menu()
        while True:
            key = get_key()
            if key:
                if key == 'q': print("Quitting..."); break
                if active_player: print("Stopping current rhythm..."); active_player.stop(); active_player.join(); active_player = None; silence_all_notes(midiout)
                if key == 'r': display_menu(); continue
                if key in AFRICAN_RHYTHMS:
                    rhythm_data = AFRICAN_RHYTHMS[key]; print(f"Playing '{rhythm_data['name']}'... (Press 'r' to stop)"); active_player = RhythmPlayer(scheduler, rhythm_data); active_player.start()
                elif key == '8':
                    print("Starting Rhythmic Mix... (Press 'r' to stop)"); r1 = AFRICAN_RHYTHMS['1']; r3 = AFRICAN_RHYTHMS['3']; active_player = RhythmicMixPlayer(scheduler, r1, r3); active_player.start()
                elif key == '9':
                    print("Starting Melodic Mix... (Press 'r' to stop)"); r1 = AFRICAN_RHYTHMS['1']; r3 = AFRICAN_RHYTHMS['3']; active_player = MelodicMixPlayer(scheduler, r1, r3); active_player.start()
            time.sleep(0.01)
    except KeyboardInterrupt: print("\nInterrupted by user.")
    finally:
        if active_player: active_player.stop()
        scheduler.stop()
        if midiout.is_port_open(): silence_all_notes(midiout); midiout.close_port(); print("MIDI port closed. Goodbye!")
if __name__ == '__main__':
    main()