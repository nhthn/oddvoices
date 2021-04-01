import json
import numpy as np
import soundfile
from typing import List, Optional

import oddvoices.corpus
import oddvoices.g2p
import oddvoices.utils
import oddvoices.phonology
import oddvoices.synth

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


def phonemes_to_segments(
    synth: oddvoices.synth.Synth, phonemes: List[str]
) -> List[str]:
    segments: List[str] = []
    for i in range(len(phonemes) - 1):
        syllableBreak = False
        phoneme_1 = phonemes[i]
        if phoneme_1 in synth.database["segments_list"]:
            segments.append(phoneme_1)
        phoneme_2_index = i + 1
        phoneme_2 = phonemes[phoneme_2_index]
        while phoneme_2 == "-" and phoneme_2_index < len(phonemes):
            syllableBreak = True
            phoneme_2_index += 1
            phoneme_2 = phonemes[phoneme_2_index]
        diphone = phoneme_1 + phoneme_2
        if diphone in synth.database["segments_list"]:
            segments.append(diphone)
            if syllableBreak:
                segments.append("-")
        else:
            if phoneme_1 + "_" in synth.database["segments_list"]:
                segments.append(phoneme_1 + "_")
            if syllableBreak:
                segments.append("-")
            if "_" + phoneme_2 in synth.database["segments_list"]:
                segments.append("_" + phoneme_2)
    return segments


def get_trim_amount(synth, syllable):
    vowel_index = 0
    for i, segment in enumerate(syllable):
        if segment in oddvoices.phonology.VOWELS:
            vowel_index = i
    final_segments = syllable[vowel_index + 1 :]
    final_segment_lengths = [
        synth.get_segment_length(segment) - synth.crossfade_length
        for segment in final_segments
    ]
    trim_amount = sum(final_segment_lengths)
    return trim_amount


def calculate_auto_trim_amounts(synth, phonemes):
    segments = phonemes_to_segments(synth, phonemes)
    trim_amounts = []
    syllable = []
    for segment in segments:
        if segment == "-":
            if len(syllable) != 0:
                trim_amounts.append(get_trim_amount(synth, syllable))
            syllable = []
        else:
            syllable.append(segment)
    trim_amounts.append(get_trim_amount(synth, syllable))
    return trim_amounts


def sing(voice_file: str, spec, out_file: str, sample_rate: Optional[float]):
    pronunciation_dict = oddvoices.g2p.read_cmudict()
    phonemes = oddvoices.g2p.pronounce_text(spec["text"], pronunciation_dict)
    syllable_count = sum([phoneme == "-" for phoneme in phonemes])

    with open(voice_file, "rb") as f:
        database = oddvoices.corpus.read_voice_file(f)
    synth = oddvoices.synth.Synth(database, sample_rate=sample_rate)

    notes = []
    for i in range(syllable_count):
        note = spec["notes"][i % len(spec["notes"])]
        if isinstance(note, str):
            note = note_string_to_midinote(note)
        note += spec.get("transposition", 0)
        frequency = oddvoices.utils.midi_note_to_hertz(note)
        notes.append(
            {
                "frequency": frequency,
                "duration": spec["durations"][i % len(spec["durations"])]
                * 60
                / spec.get("bpm", 60),
                "formant_shift": spec.get("formant_shift", 1.0),
                "phoneme_speed": spec.get("phoneme_speed", 1.0),
            }
        )
    trim_amounts = calculate_auto_trim_amounts(synth, phonemes)
    for i, note in enumerate(notes):
        note["trim"] = trim_amounts[i]

    segments = phonemes_to_segments(synth, phonemes)
    segment_indices = []
    for segment_name in segments:
        try:
            segment_index = synth.database["segments_list"].index(segment_name)
        except:
            segment_index = -1
        segment_indices.append(segment_index)

    music: dict = {
        "segments": segment_indices,
        "notes": notes,
    }

    result = oddvoices.synth.sing(synth, music)
    soundfile.write(out_file, result, samplerate=int(synth.sample_rate))


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("voice_npz")
    parser.add_argument("music_file")
    parser.add_argument("out_file")
    parser.add_argument("-s", "--sample-rate", type=float)

    args = parser.parse_args()

    music_file = args.music_file
    with open(music_file) as f:
        music = json.load(f)

    sing(args.voice_npz, music, args.out_file, sample_rate=args.sample_rate)
