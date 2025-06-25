import rtmidi
import time
import random

# Define the MIDI port name
port_name = "LoopBe Internal MIDI"  # Replace with your MIDI port name if needed

# Define the tempo (in beats per minute)
tempo = 110  # Adjust tempo for 80s pop feel

# Calculate the time per beat (in seconds)
seconds_per_beat = 60 / tempo

# Define drum notes (MIDI numbers)
kick_drum = 36
snare_drum = 38
hi_hat = 42
ride_cymbal = 51
crash_cymbal = 49
drum_channel = 9  # MIDI channel 10 is represented as 9 (0-indexed)

# Define synth instrument (MIDI program number)
synth_program = 80  # Synth Pad
sax_program = 65  # Soprano Sax

# Define chord progression (typical 80s pop - I-V-vi-IV)
chord_progression = [[60, 64, 67], [67, 71, 74], [57, 60, 64], [53, 57, 60]]  # C-G-Am-F

# Define melody notes (C major scale)
melody_notes = [60, 62, 64, 65, 67, 69, 71, 72]

# Define drum pattern (typical 80s pop)
drum_pattern = [
    [kick_drum, hi_hat],  # Beat 1
    [snare_drum, hi_hat],  # Beat 2
    [kick_drum, hi_hat],  # Beat 3
    [hi_hat],  # Beat 4
]

# Define song length (in seconds)
song_length = 180  # 3 minutes

# Define song structure
intro_length = 16 * seconds_per_beat
verse_length = 32 * seconds_per_beat
chorus_length = 32 * seconds_per_beat
bridge_length = 16 * seconds_per_beat
outro_length = 32 * seconds_per_beat

try:
    # Create a MIDI output port
    midiout = rtmidi.MidiOut()
    midiout.open_port(0)  # Open the first available port

    # Set the instrument for channel 1 (Synth Pad)
    midiout.send_message([0xC0, synth_program])
    # Set the instrument for channel 2 (Soprano Sax)
    midiout.send_message([0xC1, sax_program])  # Channel 2

except Exception as e:
    print(f"Error opening MIDI output: {e}")
    exit()


def play_section(section_length):
    start_time = time.time()
    while time.time() - start_time < section_length:
        # Choose a chord from the progression
        chord = random.choice(chord_progression)

        # Choose a melody note
        melody_note = random.choice(melody_notes)

        # Add a drum beat
        if random.random() < 0.2:  # 20% chance of a kick drum
            midiout.send_message([0x99, kick_drum, 100])  # Channel 10 (drums)
            time.sleep(0.05)
            midiout.send_message([0x89, kick_drum, 0])  # Channel 10 (drums)

        if random.random() < 0.1:  # 10% chance of a snare drum
            midiout.send_message([0x99, snare_drum, 100])  # Channel 10 (drums)
            time.sleep(0.05)
            midiout.send_message([0x89, snare_drum, 0])  # Channel 10 (drums)

        # Play the chord (polyphony) - on channel 1
        for note in chord:
            midiout.send_message([0x90, note, 60])  # Note on, channel 1

        # Play the melody note
        midiout.send_message([0x91, melody_note, 80])  # Note on, channel 2 (Sax)

        # Wait for a short amount of time
        time.sleep(seconds_per_beat / 2 - 0.05)

        # Turn off the chord notes
        for note in chord:
            midiout.send_message([0x80, note, 0])  # Note off, channel 1

        # Turn off the melody note
        midiout.send_message([0x81, melody_note, 0])  # Note off, channel 2

        # Add a small overlap
        time.sleep(0.05)


try:
    song_start = time.time()
    current_time = 0

    # Intro
    print("Playing intro...")
    play_section(intro_length)
    current_time += intro_length

    # Verse 1
    print("Playing verse 1...")
    play_section(verse_length)
    current_time += verse_length

    # Chorus
    print("Playing chorus...")
    play_section(chorus_length)
    current_time += chorus_length

    # Verse 2
    print("Playing verse 2...")
    play_section(verse_length)
    current_time += verse_length

    # Chorus
    print("Playing chorus...")
    play_section(chorus_length)
    current_time += chorus_length

    # Bridge
    print("Playing bridge...")
    play_section(bridge_length)
    current_time += bridge_length

    # Chorus
    print("Playing chorus...")
    play_section(chorus_length)
    current_time += chorus_length

    # Outro
    print("Playing outro...")
    play_section(outro_length)
    current_time += outro_length

    print("Song finished!")

except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Close the MIDI output port
    midiout.close_port()
