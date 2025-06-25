import mido

try:
    output_ports = mido.get_output_names()
    print("Available MIDI output ports:")
    for port in output_ports:
        print(port)
except Exception as e:
    print(f"Error: {e}")
