import json
import numpy as np

import phonology
import synth

pronunciation_dict = {}

NOTE_NAMES = ["c", "d", "e", "f", "g", "a", "b"]
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
FLATS = "bf"
SHARPS = "#s"

def note_string_to_midinote(string):
    if not 2 <= len(string) <= 3:
        raise ValueError(f"Note string {string} is not 2-3 characters")
    octave = int(string[-1])
    degree = NOTE_NAMES.index(string[0].lower())
    accidental = 0
    if len(string) == 3:
        accidental_string = string[1]
        if accidental_string in FLATS:
            accidental = -1
        elif accidental_string in SHARPS:
            accidental = 1
        else:
            raise ValueError(f"Invalid accidental: {accidental_string}")
    return 60 + (octave - 4) * 12 + MAJOR_SCALE[degree] + accidental


def arpabet_to_xsampa(string):
    if string[-1].isdigit():
        return phonology.ARPABET_TO_XSAMPA[string[:-1]]
    return phonology.ARPABET_TO_XSAMPA[string]


def split_syllables(word):
    result = []
    current_syllable = None
    current_syllable_has_vowel = False
    def new_syllable():
        nonlocal current_syllable
        nonlocal current_syllable_has_vowel
        current_syllable_has_vowel = False
        current_syllable = []
        result.append(current_syllable)
    new_syllable()
    for phoneme in word:
        if phoneme in phonology.VOWELS:
            if current_syllable_has_vowel:
                new_syllable()
            current_syllable_has_vowel = True
        else:
            if current_syllable_has_vowel and current_syllable[-1] in phonology.CONSONANTS:
                new_syllable()
        current_syllable.append(phoneme)

    if not current_syllable_has_vowel and len(result) > 1:
        result[-2].extend(result.pop())

    return result

if __name__ == "__main__":
    import sys

    with open(sys.argv[1]) as f:
        spec = json.load(f)

    with open("cmudict-0.7b", encoding="windows-1252") as f:
        for line in f:
            if line.startswith(";;;"):
                continue
            line = line.split()
            pronunciation_dict[line[0].lower()] = [arpabet_to_xsampa(x) for x in line[1:]]

    syllables = []
    for word in spec["text"].split():
        if word.startswith("/"):
            pronunciation = phonology.parse_pronunciation(word[1:-1])
        else:
            pronunciation = pronunciation_dict[word]
        syllables.extend(split_syllables(pronunciation))

    database = np.load("segments.npz")
    diphone_synth = synth.DiphoneSynth(database)

    music = {
        "time_scale": 1,
        "formant_shift": 1.0,
        "transpose": 0,
        "notes": []
    }

    for i, syllable in enumerate(syllables):
        note = spec["notes"][i]
        if isinstance(note, str):
            note = note_string_to_midinote(note)
        music["notes"].append({
            "midi_note": note,
            "phonemes": syllable,
            "duration": spec["durations"][i] * 60 / spec.get("bpm", 60)
        })

    diphone_synth.sing(music, "out.wav")
