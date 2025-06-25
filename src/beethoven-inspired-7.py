import rtmidi
import threading
import time
from collections import defaultdict
import sys
import select
import random

# MIDI Setup
PORT_INDEX = 0
TEMPO_BPM = 76  # Beethoven's Allegretto tempo
SECONDS_PER_BEAT = 60 / TEMPO_BPM
VELOCITY_PP = 30
VELOCITY_P = 45
VELOCITY_MP = 60
VELOCITY_MF = 75
VELOCITY_F = 90
VELOCITY_FF = 105
VELOCITY_FFF = 120

# MIDI Instrument Programs (General MIDI)
INSTRUMENTS = {
    'strings': 48,        # String Ensemble 1
    'strings2': 49,       # String Ensemble 2
    'violin': 40,         # Violin
    'viola': 41,          # Viola
    'cello': 42,          # Cello
    'contrabass': 43,     # Contrabass
    'flute': 73,          # Flute
    'oboe': 68,           # Oboe
    'clarinet': 71,       # Clarinet
    'bassoon': 70,        # Bassoon
    'horn': 60,           # French Horn
    'trumpet': 56,        # Trumpet
    'timpani': 47,        # Timpani
    'harp': 46,           # Orchestral Harp
    'choir': 52           # Voice Oohs
}

# Channel assignments
CHANNELS = {
    'violin1': 0,
    'violin2': 1,
    'viola': 2,
    'cello': 3,
    'bass': 4,
    'woodwind1': 5,
    'woodwind2': 6,
    'brass1': 7,
    'brass2': 8,
    'timpani': 9
}

# Musical modes for variety
MODES = {
    'aeolian': [0, 2, 3, 5, 7, 8, 10],      # Natural minor
    'dorian': [0, 2, 3, 5, 7, 9, 10],       # Minor with raised 6th
    'phrygian': [0, 1, 3, 5, 7, 8, 10],     # Minor with lowered 2nd
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11], # Harmonic minor
    'melodic_minor': [0, 2, 3, 5, 7, 9, 11]   # Melodic minor ascending
}

class CompositionParameters:
    """Parameters for generating a new composition"""
    def __init__(self):
        self.key_root = random.choice(['A', 'D', 'E', 'G', 'C', 'F'])
        self.mode = random.choice(list(MODES.keys()))
        self.tempo_variance = random.uniform(0.9, 1.1)  # ±10% tempo variation
        self.phrase_length = random.choice([4, 6, 8])   # Measures per phrase
        self.complexity = random.uniform(0.3, 1.0)      # Affects polyphonic density
        self.dynamic_range = random.choice(['subtle', 'moderate', 'dramatic'])
        self.texture_evolution = random.choice(['gradual', 'terraced', 'wave'])
        self.climax_position = random.uniform(0.6, 0.8)  # Where in the piece

# Convert note names to MIDI numbers
def note_to_midi(note_name):
    if note_name == 'rest':
        return None
    
    notes = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    pitch_class = note_name[0]
    octave = int(note_name[-1])
    
    midi_num = notes[pitch_class] + (octave + 1) * 12
    
    if '#' in note_name:
        midi_num += 1
    elif 'b' in note_name:
        midi_num -= 1
    
    return midi_num

def get_scale_notes(root, octave, mode):
    """Get MIDI note numbers for a scale"""
    root_midi = note_to_midi(f"{root}{octave}")
    return [root_midi + interval for interval in MODES[mode]]

def create_ostinato_pattern(params, scale_notes, pattern_type='main'):
    """Generate an ostinato pattern in Beethoven's style"""
    pattern = []
    
    # Dactyl-spondee rhythm variations
    rhythm_patterns = [
        [0.5, 0.25, 0.25, 0.5, 0.5],  # Original Beethoven pattern
        [0.75, 0.25, 0.5, 0.5],        # Variation 1
        [0.5, 0.25, 0.25, 0.25, 0.25, 0.5],  # Variation 2
        [1.0, 0.5, 0.5],               # Simplified
        [0.25, 0.25, 0.25, 0.25, 0.5, 0.5],  # More complex
    ]
    
    rhythm = random.choice(rhythm_patterns)
    
    if pattern_type == 'main':
        # Create a hypnotic pattern emphasizing one note
        emphasis_note = random.choice(scale_notes[:5])  # Lower register
        
        # Opening repetition (like Beethoven's 16 D's)
        repetitions = random.randint(8, 16)
        for i in range(repetitions // len(rhythm)):
            for duration in rhythm:
                pattern.append((emphasis_note, duration))
        
        # Melodic development
        for phrase in range(params.phrase_length):
            if random.random() < 0.7:  # 70% chance of stepwise motion
                direction = random.choice([-1, 1])
                current_idx = scale_notes.index(emphasis_note)
                
                for i in range(len(rhythm)):
                    note_idx = (current_idx + (i * direction)) % len(scale_notes)
                    pattern.append((scale_notes[note_idx], rhythm[i]))
            else:  # Leap
                for duration in rhythm:
                    note = random.choice(scale_notes)
                    pattern.append((note, duration))
    
    elif pattern_type == 'counter':
        # Lyrical counter-melody
        pattern.append((None, params.phrase_length * 2))  # Rest at start
        
        # Create flowing melodic line
        current_note = random.choice(scale_notes[3:6])  # Middle register
        for _ in range(params.phrase_length * 2):
            # Mostly stepwise with occasional leaps
            if random.random() < 0.8:
                step = random.choice([-1, 1])
                current_idx = scale_notes.index(current_note)
                new_idx = max(0, min(len(scale_notes) - 1, current_idx + step))
                current_note = scale_notes[new_idx]
            else:
                current_note = random.choice(scale_notes)
            
            duration = random.choice([0.5, 1.0, 1.5, 2.0])
            pattern.append((current_note, duration))
    
    elif pattern_type == 'bass':
        # Bass line emphasizing tonic and dominant
        tonic = scale_notes[0] - 24  # Two octaves down
        dominant = scale_notes[4] - 24
        subdominant = scale_notes[3] - 24
        
        bass_patterns = [
            [tonic, tonic, dominant, dominant],
            [tonic, subdominant, dominant, tonic],
            [tonic, dominant, tonic, dominant],
            [tonic, tonic, subdominant, dominant]
        ]
        
        bass_sequence = random.choice(bass_patterns)
        for note in bass_sequence:
            pattern.append((note, 2.0))  # Half notes
    
    return pattern

def create_harmonic_voice(scale_notes, voice_type='high'):
    """Create harmonic supporting voices"""
    pattern = []
    
    if voice_type == 'high':
        notes = scale_notes[2:7]  # Upper part of scale
    else:
        notes = scale_notes[0:5]  # Lower part
    
    # Create pattern with ostinato rhythm
    rhythm = [0.5, 0.25, 0.25, 0.5, 0.5]
    
    for _ in range(4):  # 4 measure phrase
        note = random.choice(notes)
        for duration in rhythm:
            pattern.append((note, duration))
    
    return pattern

def generate_section_plan(params):
    """Generate the formal structure of the piece"""
    sections = []
    total_beats = 0
    target_length = random.randint(200, 300)  # Total beats
    
    # Opening
    sections.append({
        'name': 'Opening: Mysterious Introduction',
        'start_beat': 0,
        'instruments': ['woodwind1', 'woodwind2'],
        'texture': 'chord',
        'dynamics': VELOCITY_PP,
        'duration': 4
    })
    total_beats += 4
    
    # Build up sections
    instrument_groups = [
        ['viola', 'cello'],
        ['violin2'],
        ['violin1'],
        ['woodwind1', 'woodwind2'],
        ['brass1'],
        ['full']
    ]
    
    section_count = 0
    while total_beats < target_length * params.climax_position:
        duration = params.phrase_length * 4
        
        if params.texture_evolution == 'gradual':
            # Gradually add instruments
            active_instruments = []
            for i in range(min(section_count + 1, len(instrument_groups))):
                active_instruments.extend(instrument_groups[i] if instrument_groups[i] != ['full'] else 
                                        list(CHANNELS.keys()))
        elif params.texture_evolution == 'terraced':
            # Jump between instrumental groups
            active_instruments = instrument_groups[section_count % len(instrument_groups)]
            if active_instruments == ['full']:
                active_instruments = list(CHANNELS.keys())
        else:  # wave
            # Build up and reduce cyclically
            wave_position = section_count % (len(instrument_groups) * 2)
            if wave_position < len(instrument_groups):
                active_instruments = instrument_groups[:wave_position + 1]
                active_instruments = [inst for group in active_instruments for inst in 
                                    (group if group != ['full'] else list(CHANNELS.keys()))]
            else:
                idx = len(instrument_groups) * 2 - wave_position - 1
                active_instruments = instrument_groups[:idx + 1]
                active_instruments = [inst for group in active_instruments for inst in 
                                    (group if group != ['full'] else list(CHANNELS.keys()))]
        
        # Dynamic progression
        if params.dynamic_range == 'subtle':
            dynamics = VELOCITY_P + (section_count * 5)
        elif params.dynamic_range == 'moderate':
            dynamics = VELOCITY_PP + (section_count * 10)
        else:  # dramatic
            dynamics = VELOCITY_PP + (section_count * 15)
        
        dynamics = min(dynamics, VELOCITY_FF)
        
        sections.append({
            'name': f'Section {section_count + 1}: Development',
            'start_beat': total_beats,
            'instruments': active_instruments,
            'texture': 'polyphonic',
            'dynamics': dynamics,
            'duration': duration
        })
        
        total_beats += duration
        section_count += 1
    
    # Climax
    climax_duration = params.phrase_length * 6
    sections.append({
        'name': 'Climax: Full Orchestra',
        'start_beat': total_beats,
        'instruments': list(CHANNELS.keys()),
        'texture': 'tutti',
        'dynamics': VELOCITY_FF if params.dynamic_range == 'dramatic' else VELOCITY_F,
        'duration': climax_duration,
        'add_timpani': True
    })
    total_beats += climax_duration
    
    # Denouement
    while total_beats < target_length:
        duration = params.phrase_length * 4
        sections.append({
            'name': f'Coda: Return to Tranquility',
            'start_beat': total_beats,
            'instruments': ['viola', 'cello'],
            'texture': 'sparse',
            'dynamics': VELOCITY_PP,
            'duration': duration
        })
        total_beats += duration
    
    # Final chord
    sections.append({
        'name': 'Final Resolution',
        'start_beat': total_beats,
        'instruments': ['woodwind1', 'woodwind2', 'viola', 'cello'],
        'texture': 'chord',
        'dynamics': VELOCITY_PP,
        'duration': 4
    })
    
    return sections

class MidiPlayer(threading.Thread):
    def __init__(self, midiout, display_callback=None):
        super().__init__(daemon=True)
        self.midiout = midiout
        self.tracks = defaultdict(list)
        self.running = True
        self.current_beat = 0
        self.start_from_beat = 0
        self.display_callback = display_callback
        self.skip_requested = None
        self.composition_info = None
        
    def add_track(self, channel, notes, start_time=0, instrument=None, velocity_mod=0):
        """Add a track with notes starting at a specific time"""
        if instrument is not None:
            self.tracks[channel].append(('program', instrument, start_time))
        
        current_time = start_time
        for note, duration in notes:
            if note is not None:
                velocity = min(127, max(1, VELOCITY_MP + velocity_mod))
                self.tracks[channel].append(('note_on', note, velocity, current_time))
                self.tracks[channel].append(('note_off', note, current_time + duration))
            current_time += duration
    
    def skip_to_section(self, section_index):
        """Skip to a specific section"""
        if 0 <= section_index < len(self.composition_info['sections']):
            self.skip_requested = self.composition_info['sections'][section_index]['start_beat']
            self.stop_all_notes()
    
    def stop_all_notes(self):
        """Send all notes off"""
        for channel in range(16):
            self.midiout.send_message([0xB0 | channel, 123, 0])
    
    def run(self):
        # Merge all events from all tracks and sort by time
        all_events = []
        for channel, events in self.tracks.items():
            for event in events:
                if event[0] == 'program':
                    all_events.append((event[2], 'program', channel, event[1]))
                elif event[0] == 'note_on':
                    all_events.append((event[3], 'note_on', channel, event[1], event[2]))
                elif event[0] == 'note_off':
                    all_events.append((event[2], 'note_off', channel, event[1]))
        
        all_events.sort(key=lambda x: x[0])
        
        # Play events
        while self.running:
            if self.skip_requested is not None:
                self.start_from_beat = self.skip_requested
                self.skip_requested = None
                
            events_to_play = [e for e in all_events if e[0] >= self.start_from_beat]
            
            start_time = time.time()
            last_beat = self.start_from_beat
            
            for event_time, event_type, channel, *params in events_to_play:
                if not self.running or self.skip_requested is not None:
                    break
                
                # Update current beat for display
                self.current_beat = event_time
                if int(self.current_beat) > int(last_beat):
                    last_beat = self.current_beat
                    if self.display_callback:
                        self.display_callback(int(self.current_beat))
                
                # Wait until the event time
                current_time = time.time() - start_time
                wait_time = ((event_time - self.start_from_beat) * SECONDS_PER_BEAT) - current_time
                if wait_time > 0:
                    time.sleep(wait_time)
                
                # Send MIDI message
                if event_type == 'program':
                    self.midiout.send_message([0xC0 | channel, params[0]])
                elif event_type == 'note_on':
                    self.midiout.send_message([0x90 | channel, params[0], params[1]])
                elif event_type == 'note_off':
                    self.midiout.send_message([0x80 | channel, params[0], 0])
            
            if self.skip_requested is None:
                break
    
    def stop(self):
        self.running = False
        self.stop_all_notes()

def clear_screen():
    """Clear the terminal screen"""
    print('\033[2J\033[H', end='')

def display_section_info(current_beat):
    """Display current section information"""
    if not hasattr(display_section_info, 'player') or not display_section_info.player:
        return
        
    composition_info = display_section_info.player.composition_info
    if not composition_info:
        return
        
    current_section = None
    current_index = 0
    for i, section in enumerate(composition_info['sections']):
        if current_beat >= section['start_beat']:
            current_section = section
            current_index = i
        else:
            break
    
    if current_section:
        clear_screen()
        print("=" * 70)
        print("ALGORITHMIC COMPOSITION in the style of Beethoven's Allegretto")
        print("=" * 70)
        print(f"\nKey: {composition_info['key']} | Mode: {composition_info['mode'].title()}")
        print(f"Texture Evolution: {composition_info['texture_evolution'].title()}")
        print(f"Dynamic Range: {composition_info['dynamic_range'].title()}")
        print(f"\nBeat: {current_beat} / ~{composition_info['total_beats']}")
        print(f"\n{current_section['name']}")
        print(f"Active Instruments: {', '.join(current_section['instruments'])}")
        print("\n" + "=" * 70)
        print("\nCONTROLS:")
        print("[R] Generate new composition  [1-9] Skip to section  [Q] Quit")
        print("\nSections:")
        for i, sec in enumerate(composition_info['sections'][:9]):  # Show max 9
            marker = "► " if sec == current_section else "  "
            print(f"{marker}[{i+1}] {sec['name']} (beat {sec['start_beat']})")

def handle_user_input(player):
    """Handle keyboard input in a separate thread"""
    while player.running:
        if sys.platform == 'win32':
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                if key == 'q':
                    player.stop()
                elif key == 'r':
                    player.stop()
                    handle_user_input.restart_requested = True
                elif key.isdigit() and 1 <= int(key) <= 9:
                    player.skip_to_section(int(key) - 1)
        else:
            # Unix/Linux/MacOS
            import termios, tty
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin.fileno())
                i, o, e = select.select([sys.stdin], [], [], 0.1)
                if i:
                    key = sys.stdin.read(1).lower()
                    if key == 'q':
                        player.stop()
                    elif key == 'r':
                        player.stop()
                        handle_user_input.restart_requested = True
                    elif key.isdigit() and 1 <= int(key) <= 9:
                        player.skip_to_section(int(key) - 1)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        time.sleep(0.1)

def create_algorithmic_composition():
    """Create a new algorithmic composition in Beethoven's style"""
    player = None
    
    # Initialize MIDI
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    if not ports:
        raise RuntimeError("No MIDI ports found.")
    midiout.open_port(PORT_INDEX)
    
    try:
        # Generate composition parameters
        params = CompositionParameters()
        
        # Get scale for the composition
        scale_notes = get_scale_notes(params.key_root, 3, params.mode)  # Start in octave 3
        scale_notes.extend(get_scale_notes(params.key_root, 4, params.mode))  # Add octave 4
        scale_notes.extend(get_scale_notes(params.key_root, 5, params.mode))  # Add octave 5
        
        # Generate musical patterns
        ostinato_theme = create_ostinato_pattern(params, scale_notes, 'main')
        counter_melody = create_ostinato_pattern(params, scale_notes, 'counter')
        bass_line = create_ostinato_pattern(params, scale_notes, 'bass')
        harmonic1 = create_harmonic_voice(scale_notes[7:14], 'high')
        harmonic2 = create_harmonic_voice(scale_notes[0:7], 'low')
        
        # Generate section plan
        sections = generate_section_plan(params)
        
        # Create player
        player = MidiPlayer(midiout, display_callback=display_section_info)
        
        # Store composition info
        total_beats = sections[-1]['start_beat'] + sections[-1]['duration']
        player.composition_info = {
            'key': f"{params.key_root} {params.mode}",
            'mode': params.mode,
            'texture_evolution': params.texture_evolution,
            'dynamic_range': params.dynamic_range,
            'sections': sections,
            'total_beats': total_beats
        }
        
        # Store player reference for display function
        display_section_info.player = player
        
        # Build the composition based on sections
        for section in sections:
            start_beat = section['start_beat']
            dynamics_mod = section['dynamics'] - VELOCITY_MP
            
            if section['texture'] == 'chord':
                # Create held chord
                chord_notes = [
                    (scale_notes[0], section['duration']),
                    (scale_notes[2], section['duration']),
                    (scale_notes[4], section['duration'])
                ]
                if 'woodwind1' in section['instruments']:
                    player.add_track(CHANNELS['woodwind1'], [chord_notes[0]], start_beat,
                                   INSTRUMENTS['clarinet'], dynamics_mod)
                if 'woodwind2' in section['instruments']:
                    player.add_track(CHANNELS['woodwind2'], [chord_notes[1]], start_beat,
                                   INSTRUMENTS['oboe'], dynamics_mod)
                if 'viola' in section['instruments']:
                    player.add_track(CHANNELS['viola'], [chord_notes[2]], start_beat,
                                   INSTRUMENTS['viola'], dynamics_mod)
            
            elif section['texture'] in ['polyphonic', 'tutti', 'sparse']:
                # Add appropriate instruments
                repetitions = section['duration'] // (params.phrase_length * 2)
                
                if 'viola' in section['instruments']:
                    player.add_track(CHANNELS['viola'], ostinato_theme * repetitions, start_beat,
                                   INSTRUMENTS['viola'], dynamics_mod)
                if 'cello' in section['instruments']:
                    player.add_track(CHANNELS['cello'], ostinato_theme * repetitions, start_beat,
                                   INSTRUMENTS['cello'], dynamics_mod)
                if 'violin2' in section['instruments']:
                    player.add_track(CHANNELS['violin2'], counter_melody * repetitions, start_beat,
                                   INSTRUMENTS['violin'], dynamics_mod)
                if 'violin1' in section['instruments']:
                    player.add_track(CHANNELS['violin1'], ostinato_theme * repetitions, start_beat,
                                   INSTRUMENTS['violin'], dynamics_mod + 5)
                if 'bass' in section['instruments']:
                    player.add_track(CHANNELS['bass'], bass_line * repetitions, start_beat,
                                   INSTRUMENTS['contrabass'], dynamics_mod - 5)
                if 'woodwind1' in section['instruments']:
                    player.add_track(CHANNELS['woodwind1'], harmonic1 * repetitions, start_beat,
                                   INSTRUMENTS['clarinet'], dynamics_mod)
                if 'woodwind2' in section['instruments']:
                    player.add_track(CHANNELS['woodwind2'], harmonic2 * repetitions, start_beat,
                                   INSTRUMENTS['oboe'], dynamics_mod)
                if 'brass1' in section['instruments']:
                    player.add_track(CHANNELS['brass1'], ostinato_theme * repetitions, start_beat,
                                   INSTRUMENTS['horn'], dynamics_mod + 10)
                
                # Add timpani to climax
                if section.get('add_timpani'):
                    timpani_pattern = []
                    for _ in range(repetitions * 4):
                        timpani_pattern.extend([
                            (scale_notes[0] - 24, 0.5), (None, 1.5),
                            (scale_notes[4] - 24, 0.5), (None, 1.5)
                        ])
                    player.add_track(CHANNELS['timpani'], timpani_pattern, start_beat,
                                   INSTRUMENTS['timpani'], dynamics_mod + 15)
        
        # Start playback
        player.start()
        
        # Start input handler
        handle_user_input.restart_requested = False
        input_thread = threading.Thread(target=handle_user_input, args=(player,), daemon=True)
        input_thread.start()
        
        # Display initial screen
        display_section_info(0)
        
        try:
            player.join()
        except KeyboardInterrupt:
            print("\nStopping performance...")
            player.stop()
        
        # Check if restart was requested
        if hasattr(handle_user_input, 'restart_requested') and handle_user_input.restart_requested:
            return True  # Signal to restart
            
    finally:
        if player:
            player.stop()
        time.sleep(0.5)  # Give time for all notes to stop
        
    return False  # Normal exit

def main():
    # Initialize MIDI once
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    if not ports:
        raise RuntimeError("No MIDI ports found.")
    
    print("=" * 70)
    print("ALGORITHMIC BEETHOVEN-STYLE COMPOSITION GENERATOR")
    print("=" * 70)
    print("\nThis program creates original compositions using the musical")
    print("principles from Beethoven's 7th Symphony, 2nd movement.")
    print("\nEach composition is unique with randomly selected:")
    print("- Key and mode (Aeolian, Dorian, Phrygian, etc.)")
    print("- Structural evolution pattern")
    print("- Dynamic range and climax position")
    print("- Melodic and rhythmic variations")
    print("\nPress any key to generate your first composition...")
    
    if sys.platform == 'win32':
        import msvcrt
        msvcrt.getch()
    else:
        input()
    
    # Keep generating new compositions until user quits
    while True:
        restart = create_algorithmic_composition()
        if not restart:
            break
    
    midiout.close_port()
    clear_screen()
    print("Thank you for exploring algorithmic composition!")

if __name__ == '__main__':
    main()