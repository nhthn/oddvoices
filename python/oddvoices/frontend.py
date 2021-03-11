import json
import numpy as np
import soundfile

import oddvoices.corpus
import oddvoices.utils
import oddvoices.phonology
import oddvoices.synth

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
        return oddvoices.phonology.ARPABET_TO_XSAMPA[string[:-1]]
    return oddvoices.phonology.ARPABET_TO_XSAMPA[string]


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
        if phoneme in oddvoices.phonology.VOWELS:
            if current_syllable_has_vowel:
                new_syllable()
            current_syllable_has_vowel = True
        else:
            if current_syllable_has_vowel and current_syllable[-1] in oddvoices.phonology.CONSONANTS:
                new_syllable()
        current_syllable.append(phoneme)

    if not current_syllable_has_vowel and len(result) > 1:
        result[-2].extend(result.pop())

    return result

def read_cmu_dict():
    with open(oddvoices.utils.BASE_DIR / "cmudict-0.7b", encoding="windows-1252") as f:
        for line in f:
            if line.startswith(";;;"):
                continue
            line = line.split()
            pronunciation_dict[line[0].lower()] = [arpabet_to_xsampa(x) for x in line[1:]]
    return pronunciation_dict


def split_words_and_strip_punctuation(text):
    words_pass_1 = text.split()
    words_pass_2 = []

    punctuation = ".!,;:\"'()[]-"
    for word in words_pass_1:
        if word.startswith("/"):
            new_word = word
            while new_word[-1] in punctuation:
                new_word = new_word[:-1]
            if not new_word.endswith("/"):
                raise RuntimeError(f"Syntax error: {new_word}")
            words_pass_2.append(new_word)
        else:
            new_word = word
            while len(new_word) != 0 and new_word[-1] in punctuation:
                new_word = new_word[:-1]
            while len(new_word) != 0 and new_word[0] in punctuation:
                new_word = new_word[1:]
            if len(new_word) != 0:
                words_pass_2.append(new_word)

    words = words_pass_2
    return words


def pronounce_unrecognized_word(word):
    phonemes = []
    keys = sorted(
        list(oddvoices.phonology.GUESS_PRONUNCIATIONS.keys()),
        key=len,
        reverse=True,
    )

    while len(word) != 0:
        for key in keys:
            if word.startswith(key):
                word = word[len(key):]
                new_phonemes = oddvoices.phonology.GUESS_PRONUNCIATIONS[key]
                if isinstance(new_phonemes, list):
                    phonemes.extend(new_phonemes)
                else:
                    phonemes.append(new_phonemes)
                break
        else:
            word = word[1:]

    phonemes_pass_2 = []
    last_phoneme = None
    for phoneme in phonemes:
        if phoneme != last_phoneme:
            phonemes_pass_2.append(phoneme)
        last_phoneme = phoneme

    phonemes = phonemes_pass_2
    return phonemes


def pronounce_text(text):
    words = split_words_and_strip_punctuation(text)

    pronunciation_dict = read_cmu_dict()
    syllables = []
    for word in words:
        if word.startswith("/"):
            pronunciation = oddvoices.phonology.parse_pronunciation(word[1:-1])
        else:
            try:
                pronunciation = pronunciation_dict[word.lower()]
            except KeyError:
                pronunciation = pronounce_unrecognized_word(word)
        pronunciation = oddvoices.phonology.normalize_pronunciation(pronunciation)
        syllables.extend(split_syllables(pronunciation))

    return syllables


def sing(voice_file, spec, out_file):
    syllables = pronounce_text(spec["text"])

    with open(voice_file, "rb") as f:
        database = oddvoices.corpus.read_voice_file(f)

    synth = oddvoices.synth.Synth(database)

    music = {
        "phonemes": [],
        "notes": [],
    }

    for i, syllable in enumerate(syllables):
        note = spec["notes"][i]
        if isinstance(note, str):
            note = note_string_to_midinote(note)
        note += spec.get("transposition", 0)
        frequency = oddvoices.utils.midi_note_to_hertz(note)
        music["notes"].append({
            "frequency": frequency,
            "duration": spec["durations"][i] * 60 / spec.get("bpm", 60),
        })
        music["phonemes"].append("-")
        music["phonemes"].extend(syllable)

    trim_amounts = oddvoices.synth.calculate_auto_trim_amounts(synth, music["phonemes"])
    for i, note in enumerate(music["notes"]):
        note["trim"] = trim_amounts[i]

    result = oddvoices.synth.sing(synth, music)
    soundfile.write(out_file, result, samplerate=int(synth.rate))


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("voice_npz")
    parser.add_argument("music_file")
    parser.add_argument("out_file")

    args = parser.parse_args()

    music_file = args.music_file
    with open(music_file) as f:
        music = json.load(f)

    sing(args.voice_npz, music, args.out_file)
