import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent


def midi_note_to_hertz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)
