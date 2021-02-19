import numpy as np
import soundfile

import phonology

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

        self.frequency = 100
        self.phase = 0.0

        self.grains = []

        self.crossfade_length = 0.03

        self.segment_id = None
        self.segment_time = 0.0
        self.old_segment_id = None
        self.old_segment_time = 0.0
        self.crossfade = 0
        self.crossfade_ramp = 0

        self.segment_queue = []
        self.vowel = False
        self.new_syllable()
        self.new_segment()

    def start_grain(self):
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

    def new_syllable(self):
        self.locked_frequency = self.frequency

    def new_segment(self):
        if len(self.segment_queue) == 0:
            self.segment_id = None
            self.segment_length = 0.0
            return
        if self.segment_queue[0] == "|":
            self.segment_queue.pop(0)
            self.new_syllable()

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
        self.grains = [grain for grain in self.grains if grain.playing]
        result = sum([grain.process() for grain in self.grains])

        self.phase += self.locked_frequency / self.rate
        if self.phase >= 1:
            self.start_grain()
            self.phase -= 1

        self.crossfade = max(self.crossfade + self.crossfade_ramp, 0.0)

        self.old_segment_time += 1 / self.rate
        self.segment_time += 1 / self.rate
        if self.segment_time >= self.segment_length - self.crossfade_length and not self.vowel:
            self.new_segment()

        return result


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    database = np.load("segments.npz")
    synth = Synth(database)

    synth.segment_queue = [
        "_h", "hE", "E", "El",
        "|", "loU", "oU", "oU_",
        "|", "_w", "w@`", "@`", "@`l", "ld", "d_",
    ]
    synth.frequency = 100

    result = []
    for i in range(int(1.0 * synth.rate)):
        result.append(synth.process())
    synth.new_segment()
    for i in range(int(1.0 * synth.rate)):
        result.append(synth.process())
    synth.new_segment()
    for i in range(int(1.0 * synth.rate)):
        result.append(synth.process())
    synth.new_segment()
    for i in range(int(1.0 * synth.rate)):
        result.append(synth.process())

    soundfile.write("out.wav", result, samplerate=int(synth.rate))
