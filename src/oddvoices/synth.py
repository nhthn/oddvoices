from typing import List

import numpy as np
import soundfile

import oddvoices.phonology


class Grain:

    def __init__(self, frame, old_frame, frame_length, crossfade):
        self.frame = frame
        self.old_frame = old_frame
        self.frame_length = frame_length
        self.crossfade = crossfade
        self.playing = True
        self.read_pos = 0

    def process(self):
        if not self.playing:
            return 0
        result = 0
        if self.frame is not None:
            result += self.frame[self.read_pos] / 32767 * (1 - self.crossfade)
        if self.old_frame is not None:
            result += self.old_frame[self.read_pos] / 32767 * self.crossfade
        self.read_pos += 1
        if self.read_pos == self.frame_length:
            self.playing = False
        return result


class Synth:

    def __init__(self, database):
        self.database = database
        self.rate: float = float(self.database["rate"])
        self.expected_f0: float = self.rate / (0.5 * self.database["grain_length"])
        self.max_frequency = 2000
        self.frame_length = self.database["grain_length"]
        self.crossfade_length = 0.03

        self.note_ons = 0
        self.note_offs = 0

        self.frequency = 0
        self.phase = 0.0

        self.grains = []

        self.segment_id = "-"
        self.segment_time = 0.0
        self.old_segment_id = None
        self.old_segment_time = 0.0
        self.crossfade = 0
        self.crossfade_ramp = 0

        self.segment_queue = []
        self.segment_is_long = False
        self._new_segment()

    def _start_grain(self):
        if self.segment_id == "-":
            return

        frame_index = int(self.segment_time * self.expected_f0)
        frame_index = frame_index % self.database["segments"][self.segment_id]["num_frames"]
        frame = self.database["segments"][self.segment_id]["frames"][frame_index, :]

        if self.old_segment_id != "-":
            old_frame_index = int(self.old_segment_time * self.expected_f0)
            old_frame_index = old_frame_index % self.database["segments"][self.old_segment_id]["num_frames"]
            old_frame = self.database["segments"][self.old_segment_id]["frames"][old_frame_index, :]
        else:
            old_frame = None

        grain = Grain(
            frame,
            old_frame,
            self.frame_length,
            crossfade=self.crossfade
        )
        self.grains.append(grain)

    def _new_segment(self):
        if len(self.segment_queue) == 0:
            self.segment_id = "-"
            self.segment_length = 0.0
            return

        self.old_segment_id = self.segment_id
        self.old_segment_time = self.segment_time

        self.segment_id = self.segment_queue.pop(0)
        self.segment_time = 0.0
        if self.segment_id == "-":
            self.segment_length = 0
            self.segment_is_long = False
        else:
            self.segment_length = self.get_segment_length(self.segment_id)
            self.segment_is_long = self.database["segments"][self.segment_id]["long"]

        if self.old_segment_id is None:
            self.crossfade = 0
            self.crossfade_ramp = 0
        else:
            self.crossfade = 1
            self.crossfade_ramp = -1 / (self.crossfade_length * self.rate)

    def get_segment_length(self, segment_id):
        return self.database["segments"][segment_id]["num_frames"] / self.expected_f0

    def is_active(self):
        return self.segment_id != "-"

    def process(self):
        if not self.is_active() and self.note_ons == 0:
            return 0.0

        if not self.is_active() and self.note_ons != 0:
            if len(self.segment_queue) == 0:
                return 0
            else:
                self.note_ons -= 1
                self._new_segment()

        if self.is_active() and self.note_offs != 0:
            if self.segment_is_long:
                self.note_offs -= 1
                self._new_segment()

        if self.segment_time >= self.segment_length - self.crossfade_length:
            if self.segment_is_long:
                self.segment_time = 0
            else:
                self._new_segment()

        if self.phase >= 1:
            if self.is_active():
                self._start_grain()
            self.phase -= 1

        self.old_segment_time += 1 / self.rate
        self.segment_time += 1 / self.rate
        self.crossfade = max(self.crossfade + self.crossfade_ramp, 0.0)
        self.phase += self.frequency / self.rate

        self.grains = [grain for grain in self.grains if grain.playing]
        result = sum([grain.process() for grain in self.grains])
        return result

    def note_on(self, frequency):
        self.note_ons += 1
        self.frequency = frequency
        self.gate = True

    def note_off(self):
        self.note_offs += 1


def phonemes_to_segments(synth: Synth, phonemes: List[str]) -> List[str]:
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
    final_segments = syllable[vowel_index + 1:]
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

def sing(synth, music):
    segments = phonemes_to_segments(synth, music["phonemes"])
    synth.segment_queue = segments

    result = []
    for i, note in enumerate(music["notes"]):
        frequency = note["frequency"]
        duration = note["duration"]
        trim = note["trim"]
        synth.note_on(frequency)
        for i in range(int((duration - trim) * synth.rate)):
            result.append(synth.process())
        synth.note_off()
        for i in range(int(trim * synth.rate)):
            result.append(synth.process())

    return np.array(result, dtype="float32")
