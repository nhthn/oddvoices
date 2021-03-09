import mido

import oddvoices.frontend


def make_music_spec_from_midi_file(midi_file):
    microseconds_per_beat = 500_000
    notes = []
    durations = []
    for message in midi_file:
        if message.type == "note_on":
            notes.append(message.note)
        elif message.type == "note_off":
            durations.append(message.time)

    return {"notes": notes, "durations": durations}


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("voice_file")
    parser.add_argument("midi_file")
    parser.add_argument("-l", "--lyrics", type=str)
    parser.add_argument("-f", "--lyrics_file", type=str)
    parser.add_argument("out_file")

    args = parser.parse_args()

    if args.lyrics is not None:
        lyrics = args.lyrics
    elif args.lyrics_file is not None:
        with open(args.lyrics_file) as f:
            lyrics = f.read()
    else:
        raise RuntimeError("You must supply either -l or -f")

    midi_file = mido.MidiFile(args.midi_file)
    spec = make_music_spec_from_midi_file(midi_file)
    spec["text"] = lyrics

    oddvoices.frontend.sing(args.voice_file, spec, args.out_file)

