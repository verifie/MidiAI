import rtmidi
import time
import random

# Define the MIDI port name
port_name = "LoopBe Internal MIDI"  # Replace with your MIDI port name if needed

# Define the tempo (in beats per minute)
tempo = 100  # Jazz tempo

# Calculate the time per beat (in seconds)
seconds_per_beat = 60 / tempo

# Define the scale (C minor blues scale)
scale = [60, 63, 65, 66, 69, 71]

# Define piano instrument (MIDI program number)
piano_program = 0  # Acoustic Grand Piano

try:
    # Create a MIDI output port
    midiout = rtmidi.MidiOut()
    midiout.open_port(0)  # Open the first available port

    # Set the instrument for channel 1 (Piano)
    midiout.send_message([0xC0, piano_program])
    midiout.send_message([0xC1, piano_program])  # Channel 2 also piano

except Exception as e:
    print(f"Error opening MIDI output: {e}")
    exit()


def play_note(channel, note, velocity, duration):
    midiout.send_message([0x90 + channel, note, velocity])  # Note on
    time.sleep(duration)
    midiout.send_message([0x80 + channel, note, 0])  # Note off


try:
    # Define chord voicings (C minor, F7, Bb, Eb)
    cm_voicing1 = [60, 63, 67]  # Root position
    cm_voicing2 = [63, 67, 72]  # 1st inversion
    f7_voicing1 = [53, 57, 60, 65]  # Root position
    f7_voicing2 = [57, 60, 65, 69]  # 1st inversion
    bb_voicing1 = [58, 62, 65]  # Root position
    bb_voicing2 = [62, 65, 70]  # 1st inversion
    eb_voicing1 = [63, 67, 70]  # Root position
    eb_voicing2 = [67, 70, 75]  # 1st inversion

    chord_voicings = [cm_voicing1, cm_voicing2, f7_voicing1, f7_voicing2,
                       bb_voicing1, bb_voicing2, eb_voicing1, eb_voicing2]

    # Define bass notes for walking bass line
    bass_notes = [48, 50, 52, 53, 55, 57, 59, 60]

    # Define rhythmic patterns
    rhythm1 = [0.5, 0.5, 1]  # Quarter, quarter, half
    rhythm2 = [0.25, 0.25, 0.5, 0.5]  # Eighth, eighth, quarter, quarter
    rhythm3 = [0.5, 0.25, 0.25, 0.5]  # Quarter, eighth, eighth, quarter
    rhythms = [rhythm1, rhythm2, rhythm3]

    # Main loop for the jazz piece
    while True:
        # Choose a chord voicing
        chord = random.choice(chord_voicings)

        # Play the chord (polyphony)
        for note in chord:
            velocity = random.randint(40, 70)  # Increased dynamics
            play_note(0, note, velocity, seconds_per_beat / 2)

        # Choose a melody note from the blues scale
        melody_note = random.choice(scale)
        melody_velocity = random.randint(50, 80)  # Increased dynamics
        melody_duration = seconds_per_beat * random.uniform(0.25, 0.75)
        play_note(1, melody_note, melody_velocity, melody_duration)

        # Choose a bass note
        bass_note = random.choice(bass_notes)
        bass_velocity = random.randint(40, 60)
        bass_duration = seconds_per_beat
        play_note(0, bass_note, bass_velocity, bass_duration)

        # Add a piano run (arpeggio)
        if random.random() < 0.15:  # Increased chance of arpeggio
            arpeggio = [60, 64, 67, 72, 76, 79, 84]  # Extended C major arpeggio
            for note in arpeggio:
                velocity = 50
                play_note(1, note, velocity, seconds_per_beat / 8)

        # Choose a rhythmic pattern
        rhythm = random.choice(rhythms)

        # Play a simple drum beat
        if random.random() < 0.3:
            midiout.send_message([0x99, 36, 80])  # Kick drum
            time.sleep(0.1)
            midiout.send_message([0x89, 36, 0])

        # Add a passing chord
        if random.random() < 0.2:
            passing_chord = [62, 65, 69]  # Dm7
            for note in passing_chord:
                velocity = 40
                play_note(0, note, velocity, seconds_per_beat / 4)

        time.sleep(seconds_per_beat / 4)  # Smaller gaps

except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Close the MIDI output port
    midiout.close_port()
