import numpy as np
import soundfile

import phonology


def midi_note_to_hertz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)


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
        result = self.frame[self.read_pos] / 32767 * (1 - self.crossfade)
        if self.crossfade != 0:
            result += self.old_frame[self.read_pos] / 32767 * self.crossfade
        self.read_pos += 1
        if self.read_pos == self.frame_length:
            self.playing = False
        return result


class Synth:

    def __init__(self, database):
        self.database = database
        self.rate: float = float(self.database["rate"])
        self.max_frequency = 2000
        self.frame_length = self.database["A"].shape[1]
        self.crossfade_length = 0.03

        self.status = "inactive"
        self.gate = False
        self.pending_note_off = False

        self.frequency = 0
        self.phase = 0.0

        self.grains = []

        self.segment_id = None
        self.segment_time = 0.0
        self.old_segment_id = None
        self.old_segment_time = 0.0
        self.crossfade = 0
        self.crossfade_ramp = 0

        self.segment_queue = []
        self.vowel = False
        self._new_syllable()
        self._new_segment()

    def _start_grain(self):
        if self.segment_id is None:
            return

        frame_index = int(self.segment_time * self.database["expected_f0"])
        frame_index = frame_index % self.database[self.segment_id].shape[0]

        if self.old_segment_id is not None:
            old_frame_index = int(self.old_segment_time * self.database["expected_f0"])
            old_frame_index = old_frame_index % self.database[self.old_segment_id].shape[0]
            old_frame = self.database[self.old_segment_id][old_frame_index, :]
        else:
            old_frame = None

        grain = Grain(
            self.database[self.segment_id][frame_index, :],
            old_frame,
            self.frame_length,
            crossfade=self.crossfade
        )
        self.grains.append(grain)

    def _new_syllable(self):
        pass

    def _new_segment(self):
        if len(self.segment_queue) == 0:
            self.status = "inactive"
            self.segment_id = None
            self.segment_length = 0.0
            return
        if self.segment_queue[0] == "-":
            self.segment_queue.pop(0)
            if self.gate:
                self._new_syllable()
            else:
                self.status = "inactive"
                return

        self.old_segment_id = self.segment_id
        self.old_segment_time = self.segment_time
        if self.old_segment_id is None:
            self.crossfade = 0
            self.crossfade_ramp = 0
        else:
            self.crossfade = 1
            self.crossfade_ramp = -1 / (self.crossfade_length * self.rate)

        self.segment_time = 0.0
        self.segment_id = self.segment_queue.pop(0)
        self.segment_length = self.database[self.segment_id].shape[0] / self.database["expected_f0"]
        self.vowel = self.segment_id in phonology.VOWELS

    def process(self):
        if self.status == "inactive":
            if self.gate:
                self.status = "active"
                self._new_segment()
            else:
                return 0.0

        self.grains = [grain for grain in self.grains if grain.playing]
        result = sum([grain.process() for grain in self.grains])

        self.phase += self.frequency / self.rate
        if self.phase >= 1:
            if self.status == "active":
                self._start_grain()
            self.phase -= 1

        self.crossfade = max(self.crossfade + self.crossfade_ramp, 0.0)

        self.old_segment_time += 1 / self.rate
        self.segment_time += 1 / self.rate
        if self.segment_time >= self.segment_length - self.crossfade_length and not self.vowel:
            self._new_segment()
        elif self.vowel and self.pending_note_off:
            self.pending_note_off = False
            self._new_segment()

        return result

    def note_on(self, frequency):
        self.pending_note_off = False
        self.frequency = frequency
        self.gate = True

    def note_off(self):
        self.pending_note_off = True


def sing(synth, music):
    segments = []
    for syllable in music["syllables"]:
        segments.append("-")
        syllable = phonology.normalize_pronunciation(syllable)
        for i in range(len(syllable) - 1):
            if syllable[i] in phonology.VOWELS:
                segments.append(syllable[i])
            diphone = syllable[i] + syllable[i + 1]
            if diphone in synth.database:
                segments.append(diphone)
            else:
                if syllable[i] + "_" in synth.database:
                    segments.append(syllable[i] + "_")
                if "_" + syllable[i + 1] in synth.database:
                    segments.append("_" + syllable[i + 1])

    synth.segment_queue = segments

    result = []
    for note in music["notes"]:
        frequency = midi_note_to_hertz(note["pitch"])
        duration = note["duration"]
        trim_amount = note.get("trim_amount", 0.1)
        synth.note_on(frequency)
        for i in range(int((duration - trim_amount) * synth.rate)):
            result.append(synth.process())
        synth.note_off()
        for i in range(int(trim_amount * synth.rate)):
            result.append(synth.process())

    return np.array(result)


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    database = np.load("segments.npz")
    synth = Synth(database)

    music = {
        'syllables': [['m', 'E', 'r'], ['i']],
        'notes': [{'pitch': 52, 'duration': 0.5}, {'pitch': 50, 'duration': 0.5}]
    }

    result = sing(synth, music)
    soundfile.write("out.wav", result, samplerate=int(synth.rate))
