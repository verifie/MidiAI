import rtmidi
import random
import time
import threading

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


def play_drums():
    try:
        start_time = time.time()
        beat_index = 0
        while time.time() - start_time < song_length:
            # Play the drum pattern
            drums = drum_pattern[beat_index % len(drum_pattern)]
            for drum_note in drums:
                midiout.send_message([0x90 + drum_channel, drum_note, 100])
                time.sleep(0.05)
                midiout.send_message([0x80 + drum_channel, drum_note, 0])

            # Increment beat index
            beat_index += 1
            time.sleep(seconds_per_beat / 2)
    except KeyboardInterrupt:
        print("Exiting drum thread...")


def play_melody():
    try:
        start_time = time.time()
        beat_index = 0
        while time.time() - start_time < song_length:
            # Choose a chord from the progression
            chord = chord_progression[beat_index % len(chord_progression)]

            # Play the chord (polyphony) - on channel 1
            for note in chord:
                midiout.send_message([0x90, note, 60])  # Note on, channel 1

            # Choose a melody note
            melody_note = melody_notes[random.randint(0, len(melody_notes) - 1)]
            midiout.send_message([0x91, melody_note, 80])  # Note on, channel 2 (Sax)

            # Vary the note length and gap
            note_length = seconds_per_beat / 2 * random.uniform(0.75, 1.25)
            gap_length = seconds_per_beat / 2 * random.uniform(0.1, 0.3)

            time.sleep(note_length)

            # Turn off the chord notes
            for note in chord:
                midiout.send_message([0x80, note, 0])  # Note off, channel 1

            # Turn off the melody note
            midiout.send_message([0x81, melody_note, 0])  # Note off, channel 2

            # Increment beat index
            beat_index += 1
            time.sleep(gap_length)
    except KeyboardInterrupt:
        print("Exiting melody thread...")


try:
    # Start the drum thread
    drum_thread = threading.Thread(target=play_drums)
    drum_thread.start()

    # Start the melody thread
    melody_thread = threading.Thread(target=play_melody)
    melody_thread.start()

    # Keep the main thread alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Close the MIDI output port
    midiout.close_port()
