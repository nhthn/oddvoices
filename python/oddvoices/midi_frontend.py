import mido

import oddvoices.frontend


def make_music_spec_from_midi_file(midi_file):
    notes = []
    durations = []
    track = midi_file.tracks[0]
    messages = [message for message in track]
    for message in messages:
        if message.type == "note_on":
            notes.append(message.note)
            time = mido.tick2second(message.time, midi_file.ticks_per_beat, 500000)
            durations.append(1.0)
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

