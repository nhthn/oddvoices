import numpy as np
import soundfile


class Grain:

    def __init__(self, frame, frame_length):
        self.frame = frame
        self.frame_length = frame_length
        self.playing = True
        self.read_pos = 0

    def process(self):
        if not self.playing:
            return 0
        result = self.frame[self.read_pos] / 32767
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

        self.segment_id = "A"
        self.segment_time = 0.0
        self.grains = []

    def start_grain(self):
        frame_index = int(self.segment_time * self.database["expected_f0"])
        frame_index = frame_index % self.database[self.segment_id].shape[0]
        grain = Grain(
            self.database[self.segment_id][frame_index, :],
            self.frame_length
        )
        self.grains.append(grain)

    def process(self):
        self.grains = [grain for grain in self.grains if grain.playing]
        result = sum([grain.process() for grain in self.grains])

        self.phase += self.frequency / self.rate
        if self.phase >= 1:
            self.start_grain()
            self.phase -= 1

        self.segment_time += 1 / self.rate

        return result


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    database = np.load("segments.npz")
    synth = Synth(database)
    result = []
    for i in range(int(3.0 * synth.rate)):
        result.append(synth.process())

    soundfile.write("out.wav", result, samplerate=int(synth.rate))
