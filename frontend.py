import json

import phonology
import diphone

pronunciation_dict = {}


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
    for word in spec["utterance"].split():
        syllables.extend(split_syllables(pronunciation_dict[word]))

    database = diphone.DiphoneDatabase(
        "nathan_h_corpus.wav", "nathan_h_corpus.txt",
        expected_f0=diphone.midi_note_to_hertz(51),
    )

    music = {
        "time_scale": 1,
        "formant_shift": 1.0,
        "transpose": 0,
        "notes": []
    }

    for i, syllable in enumerate(syllables):
        music["notes"].append({
            "midi_note": spec["notes"][i],
            "phonemes": "".join(syllable),
            "duration": spec["durations"][i] * 60 / spec.get("bpm", 60)
        })

    database.sing(music, "out.wav")
