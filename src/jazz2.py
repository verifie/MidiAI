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

    # Define more chord voicings (Am7b5, D7b9, Gm7, C7)
    am7b5_voicing1 = [57, 60, 63, 66]
    d7b9_voicing1 = [62, 65, 68, 71]
    gm7_voicing1 = [55, 58, 62, 65]
    c7_voicing1 = [60, 63, 67, 70]

    chord_voicings.extend([am7b5_voicing1, d7b9_voicing1, gm7_voicing1, c7_voicing1])

    # Define bass notes for walking bass line
    bass_notes = [48, 50, 52, 53, 55, 57, 59, 60]

    # Define rhythmic patterns
    rhythm1 = [0.5, 0.5, 1]  # Quarter, quarter, half
    rhythm2 = [0.25, 0.25, 0.5, 0.5]  # Eighth, eighth, quarter, quarter
    rhythm3 = [0.5, 0.25, 0.25, 0.5]  # Quarter, eighth, eighth, quarter
    rhythms = [rhythm1, rhythm2, rhythm3]

    # Define more rhythmic patterns (swing feel)
    rhythm4 = [0.33, 0.33, 0.34, 1]  # Swing eighths, half
    rhythm5 = [0.66, 0.34, 0.5, 0.5]  # Swing quarter-eighth, quarter, quarter
    rhythms.extend([rhythm4, rhythm5])

    # Main loop for the jazz piece
    while True:
        # Introduce a rest (probability 10%)
        if random.random() < 0.1:
            time.sleep(seconds_per_beat)  # Full beat rest
            continue

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
        if random.random() < 0.25:  # Increased chance of arpeggio
            arpeggio = [60, 64, 67, 72, 76, 79, 84]  # Extended C major arpeggio
            for note in arpeggio:
                velocity = 50
                play_note(1, note, velocity, seconds_per_beat / 8)

        # Choose a rhythmic pattern
        rhythm = random.choice(rhythms)

        # Play a simple drum beat
        if random.random() < 0.4:
            midiout.send_message([0x99, 36, 80])  # Kick drum
            time.sleep(0.1)
            midiout.send_message([0x89, 36, 0])

        # Add a passing chord (more variety)
        if random.random() < 0.3:
            passing_chord = random.choice([[62, 65, 69], [64, 67, 71], [59, 62, 65]])  # Dm7, Em7, Bbm
            for note in passing_chord:
                velocity = 40
                play_note(0, note, velocity, seconds_per_beat / 4)

        # Dynamic Variation
        if random.random() < 0.2:
            tempo_multiplier = random.uniform(0.8, 1.2)  # Slight tempo changes
            time.sleep(seconds_per_beat / 4 * tempo_multiplier)  # Apply tempo change
        else:
            time.sleep(seconds_per_beat / 4)  # Smaller gaps

except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Close the MIDI output port
    midiout.close_port()
