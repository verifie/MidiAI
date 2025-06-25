
# AI Prompt: For option 9 Make the melodies very different, add layers a complexities,, make the breakdown and buildup faster. Also change through all rhythms.


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
DRUM_CHANNEL = 9      # MIDI channel 10 (0-indexed)
MELODY_CHANNEL_1 = 0  # MIDI channel 1
MELODY_CHANNEL_2 = 1  # MIDI channel 2
MELODY_CHANNEL_3 = 2  # MIDI channel 3
MELODY_INSTRUMENT_1 = 108 # GM Program #109: Kalimba
MELODY_INSTRUMENT_2 = 12  # GM Program #13: Marimba
MELODY_INSTRUMENT_3 = 73  # GM Program #74: Flute


# ================================== RHYTHM & FILL DEFINITIONS ==================================
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

# ================================== MELODY GENERATION DATA ==================================
MELODY_SCALE = [69, 72, 74, 76, 79, 81, 84] # A minor pentatonic (A4, C5, D5, E5, G5, A5, C6)
MELODIC_PHRASES = {
    'Fanga (Liberia/Guinea)': {
        'calls': [[(0.5, 2), (1.5, 4), (2.5, 3)], [(0.75, 4), (2.25, 2), (3.25, 1)]],
        'responses': [[(0.5, 1), (1.5, 0), (2.5, -1)], [(0.75, 2), (1.75, 1), (3.25, 0)]],
        'harmonies': [[(0.5, 0), (2.5, 1)], [(0.75, 2), (2.25, 0)]]
    },
    'Kpanlogo (Ga - Ghana)': {
        'calls': [[(0, 0), (0.75, 2), (1.5, 4)], [(0.5, 4), (1.5, 3), (2.5, 2)]],
        'responses': [[(0.75, 3), (1.75, 2), (2.75, 1), (3.75, 0)], [(0.5, 1), (1.5, 0)]],
        'harmonies': [[(0, -2), (1.5, 0)], [(0.5, 2), (2.5, 1)]]
    },
    'Agbekor (Ewe - Ghana)': { # 12/8 time
        'calls': [[(0, 3), (3, 5), (6, 4)], [(2, 2), (5, 1), (8, 0)]],
        'responses': [[(0, 4), (3, 3), (6, 2), (9, 1)], [(2, 0), (5, -1), (8, -2), (11, 0)]],
        'harmonies': [[(0, 1), (6, 2)], [(3, -1), (9, 0)]]
    },
    'Bikutsi (Cameroon)': { # 6/8 time
        'calls': [[(0, 4), (1.5, 5), (3, 4)], [(0.5, 2), (2, 3), (4, 1)]],
        'responses': [[(0, 2), (1.5, 1), (3, 0)], [(0.5, 3), (2, 2), (3.5, 1), (5, 0)]],
        'harmonies': [[(0, 0), (3, 2)], [(1.5, -1), (4.5, 0)]]
    },
    'Shiko (Nigeria)': {
        'calls': [[(0, 0), (1.5, 2), (2.5, 3)], [(0.75, 4), (2, 2), (3, 1)]],
        'responses': [[(0, 1), (1, 0), (2.5, 2)], [(0.75, 2), (1.5, 1), (3.25, 0)]],
        'harmonies': [[(0, -2), (2.5, 0)], [(0.75, 1), (3.25, -1)]]
    },
    'Wassoulou (Mali)': {
        'calls': [[(0, 2), (1, 3), (2, 4)], [(0.5, 5), (2.5, 3)]],
        'responses': [[(0, 1), (1, 0), (2, -1)], [(0.5, 3), (1.5, 2), (2.5, 1), (3.5, 0)]],
        'harmonies': [[(0, 0), (2, 2)], [(0.5, 3), (2.5, 1)]]
    },
    'Moribayassa (Guinea)': {
        'calls': [[(0.75, 5), (1.75, 6), (2.75, 5)], [(0.5, 2), (1.5, 3), (2.5, 4)]],
        'responses': [[(0.75, 4), (1.75, 3), (2.75, 2), (3.75, 1)], [(0.5, 1), (1.5, 0)]],
        'harmonies': [[(0.75, 3), (2.75, 3)], [(0.5, 0), (2.5, 2)]]
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
    STATE_GROOVE, STATE_DECONSTRUCT, STATE_BREAKDOWN, STATE_BUILDUP = range(4)
    def __init__(self, scheduler, rhythm_list):
        super().__init__(daemon=True)
        self.scheduler = scheduler; self.rhythms = rhythm_list
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
    
    def _get_parts_with_channel(self, rhythm, channel):
        return {name: [(n[0], n[1], n[2], n[3], channel) for n in notes] for name, notes in rhythm['parts'].items()}

    def _handle_groove(self, current_rhythm, parts_with_channel):
        play_measures = random.randint(3, 5)
        self._play_section(current_rhythm, num_measures=play_measures, custom_parts=parts_with_channel.items())
        if random.random() < 0.9: self.state = self.STATE_DECONSTRUCT

    def _handle_deconstruct(self, current_rhythm, parts_with_channel):
        print("... Deconstructing ...")
        build_order = list(current_rhythm['build_order'])
        active_parts = build_order[:]
        for _ in range(len(build_order) - 1): # Deconstruct to one part
             if self.stop_event.is_set(): return
             build_filter = lambda p_name: p_name in active_parts
             self._play_section(current_rhythm, 1, part_filter=build_filter, custom_parts=parts_with_channel.items())
             if len(active_parts) > 1: active_parts.pop()
        self.state = self.STATE_BUILDUP

    def _handle_buildup(self, current_rhythm):
        print("... Building to next rhythm ...")
        next_rhythm_idx = (self.current_rhythm_idx + 1) % len(self.rhythms)
        next_rhythm = self.rhythms[next_rhythm_idx]
        
        current_parts = self._get_parts_with_channel(current_rhythm, DRUM_CHANNEL)
        next_parts = self._get_parts_with_channel(next_rhythm, DRUM_CHANNEL)
        
        # Start with the current core part
        current_core_part_name = [p for p in current_rhythm['build_order'] if "bell" in p.lower() or "shaker" in p.lower()][0]
        active_parts = {current_core_part_name: current_parts[current_core_part_name]}
        
        # Build up the next rhythm over 2 measures
        for i in range(2):
            if self.stop_event.is_set(): return
            
            # Add next rhythm's core part
            next_core_part_name = [p for p in next_rhythm['build_order'] if "bell" in p.lower() or "shaker" in p.lower()][0]
            active_parts[next_core_part_name] = next_parts[next_core_part_name]
            
            # Add another part from the next rhythm
            if len(next_rhythm['build_order']) > 1:
                part_to_add = next_rhythm['build_order'][1]
                active_parts[part_to_add] = next_parts[part_to_add]

            self._play_section(current_rhythm, 1, custom_parts=active_parts.items())

        # Switch to the new rhythm
        self.current_rhythm_idx = next_rhythm_idx
        print(f"---> Swapped to {next_rhythm['name']} <---")
        self.state = self.STATE_GROOVE

    def run(self):
        current_rhythm = self.rhythms[self.current_rhythm_idx]
        print(f"\n---> Starting mix with {current_rhythm['name']}...")
        while not self.stop_event.is_set():
            current_rhythm = self.rhythms[self.current_rhythm_idx]
            parts_with_channel = self._get_parts_with_channel(current_rhythm, DRUM_CHANNEL)
            
            if self.state == self.STATE_GROOVE:
                self._handle_groove(current_rhythm, parts_with_channel)
            elif self.state == self.STATE_DECONSTRUCT:
                self._handle_deconstruct(current_rhythm, parts_with_channel)
            elif self.state == self.STATE_BUILDUP:
                self._handle_buildup(current_rhythm)
    def stop(self): self.stop_event.set()

class MelodicMixPlayer(RhythmicMixPlayer):
    def __init__(self, scheduler, rhythm_list):
        super().__init__(scheduler, rhythm_list)
        self.instruments = [MELODY_INSTRUMENT_1, MELODY_INSTRUMENT_2, MELODY_INSTRUMENT_3]
        self.channels = [MELODY_CHANNEL_1, MELODY_CHANNEL_2, MELODY_CHANNEL_3]
        for i, ch in enumerate(self.channels):
            self.scheduler.midiout.send_message([0xC0 | ch, self.instruments[i]])
        print(f"Melody instruments on channels {MELODY_CHANNEL_1+1}, {MELODY_CHANNEL_2+1}, {MELODY_CHANNEL_3+1}.")
        self.last_note_idx = len(MELODY_SCALE) // 2
        self.is_call = True

    def _generate_polyphonic_phrases(self, rhythm_name, base_note_idx, lead_ch, harm_ch_1, harm_ch_2):
        phrase_lib = MELODIC_PHRASES[rhythm_name]
        
        # Generate lead part
        if self.is_call: phrase_pattern = random.choice(phrase_lib['calls'])
        else: phrase_pattern = random.choice(phrase_lib['responses'])
        self.is_call = not self.is_call
        
        lead_phrase = []
        for beat, degree in phrase_pattern:
            note_idx = max(0, min(len(MELODY_SCALE) - 1, base_note_idx + degree))
            note = MELODY_SCALE[note_idx]
            lead_phrase.append((beat, note, VEL_NORMAL, 0.4, lead_ch))
        
        # Generate harmony 1
        harmony_pattern_1 = random.choice(phrase_lib['harmonies'])
        harmony_phrase_1 = []
        for beat, degree in harmony_pattern_1:
            note_idx = max(0, min(len(MELODY_SCALE) - 1, base_note_idx + degree - 2))
            note = MELODY_SCALE[note_idx]
            harmony_phrase_1.append((beat, note, VEL_GHOST, 0.6, harm_ch_1))

        # Generate harmony 2 (long notes)
        harmony_pattern_2 = [(0, -4), (2, -2)] if rhythm_name == "Kpanlogo (Ga - Ghana)" else [(0, -4)]
        harmony_phrase_2 = []
        for beat, degree in harmony_pattern_2:
            note_idx = max(0, min(len(MELODY_SCALE) -1, base_note_idx + degree))
            note = MELODY_SCALE[note_idx]
            harmony_phrase_2.append((beat, note, VEL_GHOST - 10, 2.0, harm_ch_2))

        return lead_phrase, harmony_phrase_1, harmony_phrase_2, base_note_idx
    
    def _handle_buildup(self, current_rhythm):
        # Rotate instruments for the next section
        self.channels.append(self.channels.pop(0))
        print(f"... Swapping melody roles. Lead is now on channel {self.channels[0] + 1} ...")
        super()._handle_buildup(current_rhythm)

    def _handle_groove(self, current_rhythm, parts_with_channel):
        play_measures = random.randint(2, 3) * 2
        for _ in range(play_measures):
            if self.stop_event.is_set(): break
            
            lead_ch, harm_ch_1, harm_ch_2 = self.channels[0], self.channels[1], self.channels[2]
            lead, harm1, harm2, self.last_note_idx = self._generate_polyphonic_phrases(
                current_rhythm['name'], self.last_note_idx, lead_ch, harm_ch_1, harm_ch_2
            )
            
            all_parts = parts_with_channel.copy()
            all_parts['melody_lead'] = lead
            all_parts['melody_harmony_1'] = harm1
            all_parts['melody_harmony_2'] = harm2
            self._play_section(current_rhythm, num_measures=1, custom_parts=all_parts.items())
        
        if random.random() < 0.8:
            self.state = self.STATE_DECONSTRUCT
    
    def run(self):
        print(f"\n---> Starting Melodic Mix with {self.rhythms[0]['name']}...")
        super().run()

# ================================== Main Application ==================================
def display_menu():
    print("\n" + "="*60); print("                AFRICAN RHYTHM MIDI PLAYER"); print("="*60)
    for i in range(1, 8):
        key = str(i)
        if key in AFRICAN_RHYTHMS: val = AFRICAN_RHYTHMS[key]; print(f"  [{key}] {val['name']:<25} ({val['bpm']} BPM, {val['beats_per_measure']}/8)")
    print("-" * 60)
    print(f"  [8] Rhythmic Mix (Cycles through Rhythms 1 & 3)")
    print(f"  [9] Melodic Mix (Cycles through ALL Rhythms)")
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
                    print("Starting Rhythmic Mix... (Press 'r' to stop)"); r1 = AFRICAN_RHYTHMS['1']; r3 = AFRICAN_RHYTHMS['3']; active_player = RhythmicMixPlayer(scheduler, [r1, r3]); active_player.start()
                elif key == '9':
                    print("Starting Melodic Mix... (Press 'r' to stop)"); all_rhythms = [AFRICAN_RHYTHMS[str(i)] for i in range(1, 8)]; active_player = MelodicMixPlayer(scheduler, all_rhythms); active_player.start()
            time.sleep(0.01)
    except KeyboardInterrupt: print("\nInterrupted by user.")
    finally:
        if active_player: active_player.stop()
        scheduler.stop()
        if midiout.is_port_open(): silence_all_notes(midiout); midiout.close_port(); print("MIDI port closed. Goodbye!")
if __name__ == '__main__':
    main()