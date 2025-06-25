import rtmidi
import threading
import time
from collections import defaultdict
import sys
import select

# MIDI Setup
PORT_INDEX = 0
TEMPO_BPM = 76  # Beethoven's exact metronome marking for Allegretto
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
    'strings': 1,        # String Ensemble 1
    'strings2': 1,       # String Ensemble 2
    'violin': 1,         # Violin
    'viola': 1,          # Viola
    'cello': 1,          # Cello
    'contrabass': 1,     # Contrabass
    'flute': 1,          # Flute
    'oboe': 1,           # Oboe
    'clarinet': 1,       # Clarinet
    'bassoon': 1,        # Bassoon
    'horn': 1,           # French Horn
    'trumpet': 1,        # Trumpet
    'timpani': 1         # Timpani
}

# Channel assignments for polyphonic texture
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

# Musical sections based on the analysis
SECTIONS = [
    {
        'name': 'Opening: Woodwind Chord',
        'start_beat': 0,
        'description': 'Mysterious A minor chord with E in bass and treble,\n"the deft extinguishing of a light" after the first movement.',
        'dynamics': 'pp (pianissimo)'
    },
    {
        'name': 'Section 1: Violas and Cellos',
        'start_beat': 4,
        'description': 'The famous ostinato emerges in violas and cellos in unison,\nestablishing the hypnotic dactyl-spondee rhythm.',
        'dynamics': 'pp (pianissimo)'
    },
    {
        'name': 'Section 2: Second Violins Enter',
        'start_beat': 28,
        'description': 'Second violins take the theme while violas/cellos introduce\nthe "string of beauties" counter-melody.',
        'dynamics': 'p (piano)'
    },
    {
        'name': 'Section 3: First Violins Join',
        'start_beat': 52,
        'description': 'First violins assume the theme, creating increasingly\ncomplex polyphonic textures with all strings.',
        'dynamics': 'mp (mezzo-piano)'
    },
    {
        'name': 'Section 4: Woodwinds Enter',
        'start_beat': 76,
        'description': 'Woodwinds add color with harmonic support,\nbuilding toward the first climax.',
        'dynamics': 'mf (mezzo-forte)'
    },
    {
        'name': 'Section 5: A Major Episode',
        'start_beat': 100,
        'description': 'Contrasting material in A major (parallel major),\nthe lyrical theme presented in canon.',
        'dynamics': 'mf (mezzo-forte)'
    },
    {
        'name': 'Section 6: Fugato Development',
        'start_beat': 124,
        'description': 'Strict fugal treatment with the ostinato pattern\npassing between orchestral sections.',
        'dynamics': 'f (forte)'
    },
    {
        'name': 'Section 7: Full Orchestra Climax',
        'start_beat': 148,
        'description': 'Brass and timpani join for the emotional peak,\noverwhelming power with the full orchestra.',
        'dynamics': 'ff (fortissimo)'
    },
    {
        'name': 'Section 8: Gradual Dissolution',
        'start_beat': 172,
        'description': 'Instruments drop out one by one, the procession\nfading into the distance.',
        'dynamics': 'f → p (diminuendo)'
    },
    {
        'name': 'Section 9: Return to Opening',
        'start_beat': 196,
        'description': 'The movement concludes as it began, with the same\nquestioning A minor chord, unresolved.',
        'dynamics': 'pp (pianissimo)'
    }
]

# Convert note names to MIDI numbers
def note_to_midi(note_name):
    notes = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    if note_name == 'rest':
        return None
    
    pitch_class = note_name[0]
    octave = int(note_name[-1])
    
    midi_num = notes[pitch_class] + (octave + 1) * 12
    
    if '#' in note_name:
        midi_num += 1
    elif 'b' in note_name:
        midi_num -= 1
    
    return midi_num

# The famous ostinato pattern (dactyl-spondee: ♩ ♫ ♩ ♩)
def create_ostinato_theme():
    # The opening emphasizes D, repeated 16 times before moving
    theme = []
    
    # First 4 measures: D emphasis
    for _ in range(4):
        theme.extend([
            ('D4', 0.5), ('D4', 0.25), ('D4', 0.25), ('D4', 0.5), ('D4', 0.5)
        ])
    
    # Next phrases with melodic movement
    theme.extend([
        ('E4', 0.5), ('E4', 0.25), ('E4', 0.25), ('E4', 0.5), ('E4', 0.5),
        ('F4', 0.5), ('F4', 0.25), ('F4', 0.25), ('F4', 0.5), ('F4', 0.5),
        ('E4', 0.5), ('E4', 0.25), ('E4', 0.25), ('E4', 0.5), ('E4', 0.5),
        ('D4', 0.5), ('D4', 0.25), ('D4', 0.25), ('D4', 0.5), ('D4', 0.5),
        
        ('C4', 0.5), ('C4', 0.25), ('C4', 0.25), ('C4', 0.5), ('C4', 0.5),
        ('B3', 0.5), ('B3', 0.25), ('B3', 0.25), ('B3', 0.5), ('B3', 0.5),
        ('A3', 0.5), ('A3', 0.25), ('A3', 0.25), ('A3', 0.5), ('A3', 0.5),
        ('A3', 0.5), ('A3', 0.25), ('A3', 0.25), ('A3', 0.5), ('A3', 0.5),
    ])
    
    return [(note_to_midi(n), d) for n, d in theme]

# The lyrical counter-melody ("string of beauties")
def create_counter_melody():
    melody = [
        ('rest', 2), ('rest', 2),  # Enter after theme established
        ('E5', 1), ('D5', 0.5), ('C5', 0.5), ('B4', 1), ('A4', 1),
        ('G4', 1), ('F#4', 0.5), ('G4', 0.5), ('A4', 1), ('B4', 1),
        ('C5', 1), ('D5', 0.5), ('E5', 0.5), ('F5', 1), ('E5', 1),
        ('D5', 1), ('C5', 0.5), ('B4', 0.5), ('A4', 1), ('G#4', 1),
        ('A4', 2), ('rest', 2),
    ]
    return [(note_to_midi(n) if n != 'rest' else None, d) for n, d in melody]

# Bass line supporting the harmonic progression
def create_bass_line():
    bass = [
        # Opening: A minor with E in bass (6/4 position)
        ('E2', 2), ('E2', 2), ('A2', 2), ('A2', 2),
        ('D3', 2), ('D3', 2), ('E3', 2), ('E3', 2),
        ('F3', 2), ('F3', 2), ('E3', 2), ('E3', 2),
        ('D3', 2), ('D3', 2), ('C3', 2), ('B2', 2),
        ('A2', 2), ('G#2', 2), ('A2', 2), ('A2', 2),
    ]
    return [(note_to_midi(n), d) for n, d in bass]

# Harmonic support voices
def create_harmonic_voice1():
    harmony = [
        ('C5', 0.5), ('C5', 0.25), ('C5', 0.25), ('C5', 0.5), ('C5', 0.5),
        ('B4', 0.5), ('B4', 0.25), ('B4', 0.25), ('B4', 0.5), ('B4', 0.5),
        ('A4', 0.5), ('A4', 0.25), ('A4', 0.25), ('A4', 0.5), ('A4', 0.5),
        ('G#4', 0.5), ('G#4', 0.25), ('G#4', 0.25), ('G#4', 0.5), ('G#4', 0.5),
        ('A4', 2), ('rest', 2), ('rest', 2), ('rest', 2),
    ]
    return [(note_to_midi(n) if n != 'rest' else None, d) for n, d in harmony]

def create_harmonic_voice2():
    harmony = [
        ('E4', 0.5), ('E4', 0.25), ('E4', 0.25), ('E4', 0.5), ('E4', 0.5),
        ('F4', 0.5), ('F4', 0.25), ('F4', 0.25), ('F4', 0.5), ('F4', 0.5),
        ('E4', 0.5), ('E4', 0.25), ('E4', 0.25), ('E4', 0.5), ('E4', 0.5),
        ('D4', 0.5), ('D4', 0.25), ('D4', 0.25), ('D4', 0.5), ('D4', 0.5),
        ('C4', 2), ('B3', 2), ('C4', 2), ('rest', 2),
    ]
    return [(note_to_midi(n) if n != 'rest' else None, d) for n, d in harmony]

# Woodwind parts
def create_woodwind_chord():
    # Opening A minor chord with E emphasis
    return [
        ('A4', 4), ('E5', 4), ('C5', 4), ('E4', 4)  # Held chord
    ]

# Timpani for climactic sections
def create_timpani_pattern():
    # Emphasizing A and E (tonic and dominant)
    return [
        ('A2', 0.5), ('rest', 0.5), ('rest', 0.5), ('rest', 0.5),
        ('E2', 0.5), ('rest', 0.5), ('rest', 0.5), ('rest', 0.5),
        ('A2', 0.5), ('rest', 0.5), ('A2', 0.5), ('rest', 0.5),
        ('E2', 0.5), ('rest', 0.5), ('E2', 0.5), ('rest', 0.5),
    ]

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
        
    def add_track(self, channel, notes, start_time=0, instrument=None, velocity_mod=0):
        """Add a track with notes starting at a specific time"""
        if instrument is not None:
            self.tracks[channel].append(('program', instrument, start_time))
        
        current_time = start_time
        for note, duration in notes:
            if note is not None:
                velocity = min(127, max(1, VELOCITY_P + velocity_mod))
                self.tracks[channel].append(('note_on', note, velocity, current_time))
                self.tracks[channel].append(('note_off', note, current_time + duration))
            current_time += duration
    
    def skip_to_section(self, section_index):
        """Skip to a specific section"""
        if 0 <= section_index < len(SECTIONS):
            self.skip_requested = SECTIONS[section_index]['start_beat']
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
    current_section = None
    for i, section in enumerate(SECTIONS):
        if current_beat >= section['start_beat']:
            current_section = section
            current_index = i
        else:
            break
    
    if current_section:
        clear_screen()
        print("=" * 70)
        print("BEETHOVEN'S 7TH SYMPHONY - 2nd Movement (Allegretto in A minor)")
        print("=" * 70)
        print(f"\nMeasure ~{current_beat // 2} | Beat: {current_beat} / 278")
        print(f"\n{current_section['name']}")
        print(f"Dynamics: {current_section['dynamics']}")
        print(f"\n{current_section['description']}")
        print("\n" + "=" * 70)
        print("\nCONTROLS:")
        print("[1-9] Skip to section  [Q] Quit")
        print("\nSections:")
        for i, sec in enumerate(SECTIONS):
            marker = "► " if sec == current_section else "  "
            print(f"{marker}[{i+1}] {sec['name'].split(':')[0]} (beat {sec['start_beat']})")

def handle_user_input(player):
    """Handle keyboard input in a separate thread"""
    while player.running:
        if sys.platform == 'win32':
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                if key == 'q':
                    player.stop()
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
                    elif key.isdigit() and 1 <= int(key) <= 9:
                        player.skip_to_section(int(key) - 1)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        time.sleep(0.1)

def create_full_arrangement():
    """Create the authentic Beethoven 7th Symphony, 2nd movement"""
    player = None
    
    # Initialize MIDI
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    if not ports:
        raise RuntimeError("No MIDI ports found.")
    midiout.open_port(PORT_INDEX)
    
    try:
        player = MidiPlayer(midiout, display_callback=display_section_info)
        
        # Get the musical patterns
        ostinato_theme = create_ostinato_theme()
        counter_melody = create_counter_melody()
        bass_line = create_bass_line()
        harmonic1 = create_harmonic_voice1()
        harmonic2 = create_harmonic_voice2()
        woodwind_chord = [(note_to_midi(n), d) for n, d in create_woodwind_chord()]
        timpani = [(note_to_midi(n) if n != 'rest' else None, d) for n, d in create_timpani_pattern()]
        
        # Opening: Woodwind chord (0-4 beats)
        player.add_track(CHANNELS['woodwind1'], woodwind_chord[:2], 0, 
                        INSTRUMENTS['clarinet'], velocity_mod=-25)
        player.add_track(CHANNELS['woodwind2'], woodwind_chord[2:], 0, 
                        INSTRUMENTS['oboe'], velocity_mod=-25)
        
        # Section 1: Violas and Cellos in unison (4-28 beats)
        player.add_track(CHANNELS['viola'], ostinato_theme, 4, 
                        INSTRUMENTS['viola'], velocity_mod=-25)
        player.add_track(CHANNELS['cello'], ostinato_theme, 4, 
                        INSTRUMENTS['cello'], velocity_mod=-25)
        
        # Section 2: Second Violins with counter-melody (28-52 beats)
        player.add_track(CHANNELS['violin2'], ostinato_theme, 28, 
                        INSTRUMENTS['violin'], velocity_mod=-15)
        player.add_track(CHANNELS['viola'], counter_melody, 28, 
                        velocity_mod=-10)
        player.add_track(CHANNELS['cello'], bass_line, 28, 
                        velocity_mod=-10)
        
        # Section 3: First Violins join (52-76 beats)
        player.add_track(CHANNELS['violin1'], ostinato_theme, 52, 
                        INSTRUMENTS['violin'], velocity_mod=0)
        player.add_track(CHANNELS['violin2'], counter_melody, 52, 
                        velocity_mod=0)
        player.add_track(CHANNELS['viola'], harmonic1, 52, 
                        velocity_mod=0)
        player.add_track(CHANNELS['cello'], bass_line, 52, 
                        velocity_mod=0)
        player.add_track(CHANNELS['bass'], bass_line, 52, 
                        INSTRUMENTS['contrabass'], velocity_mod=-5)
        
        # Section 4: Woodwinds enter (76-100 beats)
        player.add_track(CHANNELS['woodwind1'], harmonic1, 76, 
                        INSTRUMENTS['clarinet'], velocity_mod=5)
        player.add_track(CHANNELS['woodwind2'], harmonic2, 76, 
                        INSTRUMENTS['oboe'], velocity_mod=5)
        player.add_track(CHANNELS['violin1'], ostinato_theme, 76, 
                        velocity_mod=10)
        player.add_track(CHANNELS['violin2'], counter_melody, 76, 
                        velocity_mod=10)
        player.add_track(CHANNELS['viola'], harmonic1, 76, 
                        velocity_mod=10)
        player.add_track(CHANNELS['cello'], bass_line, 76, 
                        velocity_mod=10)
        player.add_track(CHANNELS['bass'], bass_line, 76, 
                        velocity_mod=5)
        
        # Section 5: A Major episode (100-124 beats)
        # Modulate theme to A major
        major_theme = [(note + 1 if note else None, d) for note, d in counter_melody]
        player.add_track(CHANNELS['violin1'], major_theme, 100, 
                        velocity_mod=15)
        player.add_track(CHANNELS['violin2'], major_theme, 102,  # Canon at 2 beats
                        velocity_mod=10)
        player.add_track(CHANNELS['viola'], ostinato_theme, 100, 
                        velocity_mod=10)
        player.add_track(CHANNELS['cello'], bass_line, 100, 
                        velocity_mod=10)
        
        # Section 6: Fugato development (124-148 beats)
        # Staggered entrances creating fugal texture
        player.add_track(CHANNELS['cello'], ostinato_theme, 124, 
                        velocity_mod=20)
        player.add_track(CHANNELS['viola'], ostinato_theme, 128, 
                        velocity_mod=20)
        player.add_track(CHANNELS['violin2'], ostinato_theme, 132, 
                        velocity_mod=20)
        player.add_track(CHANNELS['violin1'], ostinato_theme, 136, 
                        velocity_mod=25)
        player.add_track(CHANNELS['bass'], bass_line, 124, 
                        velocity_mod=20)
        
        # Section 7: Full orchestra climax (148-172 beats)
        player.add_track(CHANNELS['brass1'], ostinato_theme, 148, 
                        INSTRUMENTS['horn'], velocity_mod=35)
        player.add_track(CHANNELS['brass2'], harmonic1, 148, 
                        INSTRUMENTS['trumpet'], velocity_mod=30)
        player.add_track(CHANNELS['timpani'], timpani * 6, 148, 
                        INSTRUMENTS['timpani'], velocity_mod=40)
        player.add_track(CHANNELS['violin1'], ostinato_theme, 148, 
                        velocity_mod=40)
        player.add_track(CHANNELS['violin2'], counter_melody, 148, 
                        velocity_mod=35)
        player.add_track(CHANNELS['viola'], harmonic1, 148, 
                        velocity_mod=35)
        player.add_track(CHANNELS['cello'], bass_line, 148, 
                        velocity_mod=35)
        player.add_track(CHANNELS['bass'], bass_line, 148, 
                        velocity_mod=35)
        player.add_track(CHANNELS['woodwind1'], harmonic1, 148, 
                        velocity_mod=30)
        player.add_track(CHANNELS['woodwind2'], harmonic2, 148, 
                        velocity_mod=30)
        
        # Section 8: Gradual dissolution (172-196 beats)
        player.add_track(CHANNELS['violin1'], ostinato_theme, 172, 
                        velocity_mod=15)
        player.add_track(CHANNELS['violin2'], counter_melody, 172, 
                        velocity_mod=10)
        player.add_track(CHANNELS['viola'], ostinato_theme, 172, 
                        velocity_mod=5)
        player.add_track(CHANNELS['cello'], bass_line, 172, 
                        velocity_mod=0)
        
        # Continue diminuendo
        player.add_track(CHANNELS['viola'], ostinato_theme, 184, 
                        velocity_mod=-10)
        player.add_track(CHANNELS['cello'], bass_line, 184, 
                        velocity_mod=-15)
        
        # Section 9: Return to opening (196+ beats)
        player.add_track(CHANNELS['viola'], ostinato_theme, 196, 
                        velocity_mod=-25)
        player.add_track(CHANNELS['cello'], ostinato_theme, 196, 
                        velocity_mod=-25)
        
        # Final woodwind chord
        player.add_track(CHANNELS['woodwind1'], woodwind_chord[:2], 272, 
                        velocity_mod=-30)
        player.add_track(CHANNELS['woodwind2'], woodwind_chord[2:], 272, 
                        velocity_mod=-30)
        
        # Start playback
        player.start()
        
        # Start input handler
        input_thread = threading.Thread(target=handle_user_input, args=(player,), daemon=True)
        input_thread.start()
        
        # Display initial screen
        display_section_info(0)
        
        try:
            player.join()
        except KeyboardInterrupt:
            print("\nStopping performance...")
            player.stop()
            
    finally:
        if player:
            player.stop()
        time.sleep(0.5)  # Give time for all notes to stop
        midiout.close_port()
        clear_screen()
        print("Performance ended. Thank you for listening to Beethoven's masterpiece!")

def main():
    create_full_arrangement()

if __name__ == '__main__':
    main()