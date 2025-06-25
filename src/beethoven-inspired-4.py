import rtmidi
import threading
import time
from collections import defaultdict
import random
import sys
import select

# MIDI Setup
PORT_INDEX = 0
TEMPO_BPM = 76  # Allegretto tempo for Beethoven's 7th, 2nd movement
SECONDS_PER_BEAT = 60 / TEMPO_BPM
VELOCITY_PP = 40
VELOCITY_P = 55
VELOCITY_MP = 70
VELOCITY_MF = 85
VELOCITY_F = 100
VELOCITY_FF = 115

# MIDI Instrument Programs (General MIDI)
INSTRUMENTS = {
    'strings': 48,      # String Ensemble
    'viola': 41,        # Viola
    'cello': 42,        # Cello
    'oboe': 68,         # Oboe
    'clarinet': 71,     # Clarinet
    'bassoon': 70,      # Bassoon
    'horn': 60,         # French Horn
    'trumpet': 56,      # Trumpet
    'timpani': 47,      # Timpani
    'piano': 0          # Acoustic Grand Piano
}

# Channel assignments
CHANNELS = {
    'melody': 0,
    'counter': 1,
    'bass': 2,
    'harmony1': 3,
    'harmony2': 4,
    'percussion': 9  # Channel 10 is percussion
}

# Musical sections definition
SECTIONS = [
    {
        'name': 'Section 1: Solo Strings Introduction',
        'start_beat': 0,
        'description': 'The haunting main theme emerges softly in the strings alone,\nestablishing the iconic rhythmic ostinato pattern.',
        'dynamics': 'pp (pianissimo)'
    },
    {
        'name': 'Section 2: Bass Foundation',
        'start_beat': 32,
        'description': 'Cellos enter with a walking bass line, providing harmonic\ngrounding while maintaining the mysterious atmosphere.',
        'dynamics': 'p (piano)'
    },
    {
        'name': 'Section 3: Contrapuntal Development',
        'start_beat': 64,
        'description': 'Violas introduce a flowing counter-melody, creating a\nrich dialogue between the voices as tension builds.',
        'dynamics': 'mp (mezzo-piano)'
    },
    {
        'name': 'Section 4: Woodwind Colors',
        'start_beat': 96,
        'description': 'Clarinet and oboe join with harmonic voices, painting\nthe texture with warmer tones and fuller orchestration.',
        'dynamics': 'mf (mezzo-forte)'
    },
    {
        'name': 'Section 5: Brass Proclamation',
        'start_beat': 128,
        'description': 'French horns enter majestically, transforming the\nprocessional into a powerful statement of the theme.',
        'dynamics': 'f (forte)'
    },
    {
        'name': 'Section 6: Triumphant Climax',
        'start_beat': 160,
        'description': 'Full orchestra with timpani accents creates the emotional\npeak, the rhythm driving forward with unstoppable momentum.',
        'dynamics': 'ff (fortissimo)'
    },
    {
        'name': 'Section 7: Gradual Retreat',
        'start_beat': 192,
        'description': 'The storm subsides as instruments drop out one by one,\nthe dynamics fading like a procession moving into distance.',
        'dynamics': 'mf → p (diminuendo)'
    },
    {
        'name': 'Section 8: Ethereal Conclusion',
        'start_beat': 224,
        'description': 'Return to the opening texture with strings, now transformed\nby the journey, ending with a peaceful resolution.',
        'dynamics': 'pp (pianissimo)'
    }
]

# Note definitions
class Note:
    def __init__(self, pitch, duration, velocity=VELOCITY_MP, channel=0):
        self.pitch = pitch
        self.duration = duration
        self.velocity = velocity
        self.channel = channel

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

# The main theme (ostinato rhythm pattern)
def create_main_theme():
    # The iconic rhythm: quarter, two eighths, two eighths, quarter, quarter
    theme = [
        ('E4', 1), ('E4', 0.5), ('E4', 0.5), ('E4', 0.5), ('E4', 0.5), ('E4', 1), ('E4', 1),
        ('D4', 1), ('D4', 0.5), ('D4', 0.5), ('D4', 0.5), ('D4', 0.5), ('D4', 1), ('D4', 1),
        ('C4', 1), ('C4', 0.5), ('C4', 0.5), ('C4', 0.5), ('C4', 0.5), ('C4', 1), ('C4', 1),
        ('B3', 1), ('B3', 0.5), ('B3', 0.5), ('B3', 0.5), ('B3', 0.5), ('B3', 1), ('B3', 1),
    ]
    return [(note_to_midi(n), d) for n, d in theme]

# Counter melody that enters later
def create_counter_melody():
    counter = [
        ('rest', 2), ('G4', 2), ('F#4', 2), ('G4', 2),
        ('A4', 2), ('G4', 2), ('F#4', 2), ('E4', 2),
        ('D4', 2), ('C4', 2), ('B3', 2), ('A3', 2),
        ('G3', 2), ('F#3', 2), ('E3', 2), ('rest', 2),
    ]
    return [(note_to_midi(n) if n != 'rest' else None, d) for n, d in counter]

# Bass line
def create_bass_line():
    bass = [
        ('A2', 4), ('A2', 4), ('D3', 4), ('A2', 4),
        ('E3', 4), ('E3', 4), ('A2', 4), ('A2', 4),
        ('D3', 4), ('D3', 4), ('G2', 4), ('G2', 4),
        ('C3', 4), ('C3', 4), ('E3', 4), ('E3', 4),
    ]
    return [(note_to_midi(n), d) for n, d in bass]

# Harmony voices
def create_harmony1():
    harmony = [
        ('C5', 1), ('C5', 1), ('B4', 1), ('A4', 1),
        ('G4', 1), ('F#4', 1), ('E4', 1), ('D4', 1),
        ('E4', 1), ('F#4', 1), ('G4', 1), ('A4', 1),
        ('B4', 1), ('C5', 1), ('D5', 1), ('E5', 1),
    ]
    return [(note_to_midi(n), d) for n, d in harmony]

def create_harmony2():
    harmony = [
        ('A4', 2), ('G4', 2), ('F#4', 2), ('E4', 2),
        ('D4', 2), ('C4', 2), ('B3', 2), ('A3', 2),
        ('B3', 2), ('C4', 2), ('D4', 2), ('E4', 2),
        ('F#4', 2), ('G4', 2), ('A4', 2), ('B4', 2),
    ]
    return [(note_to_midi(n), d) for n, d in harmony]

class MidiPlayer(threading.Thread):
    def __init__(self, midiout, display_callback=None):
        super().__init__(daemon=True)
        self.midiout = midiout
        self.tracks = defaultdict(list)
        self.running = True
        self.current_beat = 0
        self.start_from_beat = 0
        self.display_callback = display_callback
        self.paused = False
        self.skip_requested = None
        
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
                # Find events starting from the requested beat
                self.start_from_beat = self.skip_requested
                self.skip_requested = None
                
            # Filter events based on start position
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
            
            # If we played through everything without interruption, we're done
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
        print(f"BEETHOVEN'S 7TH SYMPHONY - 2nd Movement (Allegretto)")
        print("=" * 70)
        print(f"\nBeat: {current_beat} / 260")
        print(f"\n{current_section['name']}")
        print(f"Dynamics: {current_section['dynamics']}")
        print(f"\n{current_section['description']}")
        print("\n" + "=" * 70)
        print("\nCONTROLS:")
        print("[1-8] Skip to section  [Q] Quit")
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
                elif key.isdigit() and 1 <= int(key) <= 8:
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
                    elif key.isdigit() and 1 <= int(key) <= 8:
                        player.skip_to_section(int(key) - 1)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        time.sleep(0.1)

def create_full_arrangement():
    """Create the full 5-minute arrangement"""
    player = None
    
    # Initialize MIDI
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    if not ports:
        raise RuntimeError("No MIDI ports found.")
    midiout.open_port(PORT_INDEX)
    
    try:
        player = MidiPlayer(midiout, display_callback=display_section_info)
        
        # Get the basic patterns
        main_theme = create_main_theme()
        counter_melody = create_counter_melody()
        bass_line = create_bass_line()
        harmony1 = create_harmony1()
        harmony2 = create_harmony2()
        
        # Structure: Build up layers gradually
        # Section 1: Solo strings with main theme (0-32 beats)
        player.add_track(CHANNELS['melody'], main_theme * 2, 0, 
                        INSTRUMENTS['strings'], velocity_mod=-20)
        
        # Section 2: Add bass (32-64 beats)
        player.add_track(CHANNELS['bass'], bass_line * 2, 32, 
                        INSTRUMENTS['cello'], velocity_mod=-10)
        
        # Section 3: Add counter melody with violas (64-96 beats)
        player.add_track(CHANNELS['counter'], counter_melody * 2, 64, 
                        INSTRUMENTS['viola'], velocity_mod=0)
        player.add_track(CHANNELS['melody'], main_theme * 2, 64, 
                        velocity_mod=0)
        player.add_track(CHANNELS['bass'], bass_line * 2, 64, 
                        velocity_mod=0)
        
        # Section 4: Full ensemble with woodwinds (96-128 beats)
        player.add_track(CHANNELS['harmony1'], harmony1 * 2, 96, 
                        INSTRUMENTS['clarinet'], velocity_mod=10)
        player.add_track(CHANNELS['harmony2'], harmony2 * 2, 96, 
                        INSTRUMENTS['oboe'], velocity_mod=5)
        player.add_track(CHANNELS['melody'], main_theme * 2, 96, 
                        velocity_mod=10)
        player.add_track(CHANNELS['counter'], counter_melody * 2, 96, 
                        velocity_mod=10)
        player.add_track(CHANNELS['bass'], bass_line * 2, 96, 
                        velocity_mod=10)
        
        # Section 5: Brass enters (128-160 beats)
        player.add_track(CHANNELS['melody'], main_theme * 2, 128, 
                        INSTRUMENTS['horn'], velocity_mod=20)
        player.add_track(CHANNELS['counter'], counter_melody * 2, 128, 
                        velocity_mod=15)
        player.add_track(CHANNELS['bass'], bass_line * 2, 128, 
                        velocity_mod=15)
        player.add_track(CHANNELS['harmony1'], harmony1 * 2, 128, 
                        velocity_mod=15)
        player.add_track(CHANNELS['harmony2'], harmony2 * 2, 128, 
                        velocity_mod=15)
        
        # Section 6: Fortissimo with timpani accents (160-192 beats)
        # Create timpani hits on strong beats
        timpani_pattern = [
            ('A2', 1), ('rest', 3), ('D3', 1), ('rest', 3),
            ('E3', 1), ('rest', 3), ('A2', 1), ('rest', 3)
        ]
        timpani_notes = [(note_to_midi(n) if n != 'rest' else None, d) 
                        for n, d in timpani_pattern]
        
        player.add_track(CHANNELS['percussion'], timpani_notes * 2, 160, 
                        INSTRUMENTS['timpani'], velocity_mod=30)
        player.add_track(CHANNELS['melody'], main_theme * 2, 160, 
                        velocity_mod=30)
        player.add_track(CHANNELS['counter'], counter_melody * 2, 160, 
                        velocity_mod=25)
        player.add_track(CHANNELS['bass'], bass_line * 2, 160, 
                        velocity_mod=25)
        
        # Section 7: Gradual diminuendo (192-224 beats)
        player.add_track(CHANNELS['melody'], main_theme * 2, 192, 
                        velocity_mod=10)
        player.add_track(CHANNELS['counter'], counter_melody * 2, 192, 
                        velocity_mod=5)
        player.add_track(CHANNELS['bass'], bass_line * 2, 192, 
                        velocity_mod=5)
        
        # Section 8: Quiet ending with just strings (224-256 beats)
        player.add_track(CHANNELS['melody'], main_theme * 2, 224, 
                        INSTRUMENTS['strings'], velocity_mod=-25)
        player.add_track(CHANNELS['bass'], bass_line * 2, 224, 
                        velocity_mod=-20)
        
        # Final chord (256-260 beats)
        final_chord = [
            ('A3', 4), ('C4', 4), ('E4', 4), ('A4', 4)
        ]
        final_notes = [(note_to_midi(n), d) for n, d in final_chord]
        player.add_track(CHANNELS['melody'], [final_notes[2]], 256, velocity_mod=-10)
        player.add_track(CHANNELS['counter'], [final_notes[1]], 256, velocity_mod=-10)
        player.add_track(CHANNELS['bass'], [final_notes[0]], 256, velocity_mod=-10)
        player.add_track(CHANNELS['harmony1'], [final_notes[3]], 256, velocity_mod=-10)
        
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
        print("Performance ended. Thank you for listening!")

def main():
    create_full_arrangement()

if __name__ == '__main__':
    main()