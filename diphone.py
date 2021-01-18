import soundfile
import scipy.signal
import numpy as np

import phonetics

def get_sublist_index(list_1, list_2):
    for i in range(len(list_2) - len(list_1) + 1):
        if list(list_1) == list_2[i : i + len(list_1)]:
            return i
    raise IndexError("Sublist not found")

class DiphoneDatabase:

    def __init__(self, sound_file, words_file):
        self.bpm: float = 60.0
        self.beat: float = 60 / self.bpm
        self.audio: np.array
        self.rate: int
        self.audio, self.rate = soundfile.read(sound_file)
        self.audio = np.sum(self.audio, axis=1)

        with open(words_file) as f:
            self.words = phonetics.parse_words(f)

        beat = 0
        for word in self.words:
            half_notes = word["vowel_count"] + 1
            if half_notes % 2 == 1:
                half_notes += 1
            quarter_notes = half_notes * 2
            duration = word["vowel_count"] * 2.1
            word["start_beat"] = beat
            word["end_beat"] = beat + duration
            beat += quarter_notes

    def beat_to_frame(self, beat):
        return int(self.beat * self.rate * beat)

    def do_psola(self, segment, out_f0=100.0):
        expected_f0: float = 440 * 2 ** ((52 - 69) / 12)
        period: float = self.rate / expected_f0

        frames = []

        current_measured_period = period
        offset = 0
        while True:
            window_size: int = int(current_measured_period * 3)
            if offset + window_size >= len(segment):
                break
            unwindowed_frame: np.array = segment[offset:offset + window_size]
            frame: np.array = unwindowed_frame * scipy.signal.get_window("hann", window_size)

            autocorrelation: np.array = scipy.signal.correlate(frame, frame)
            autocorrelation = autocorrelation[window_size:]
            ascending_bins = np.where(np.diff(autocorrelation) >= 0)
            if len(ascending_bins[0]) == 0:
                continue
            first_ascending_bin = np.min(ascending_bins)
            measured_period: int = np.argmax(autocorrelation[first_ascending_bin:]) + first_ascending_bin
            f0 = self.rate / measured_period
            if expected_f0 / 1.5 <= f0 <= expected_f0 * 1.5:
                period_scale_factor = period / measured_period
                current_measured_period = measured_period
            else:
                period_scale_factor = 1
                current_measured_period = period
            corrected_frame: np.array = scipy.signal.resample(frame, int(window_size * period_scale_factor))
            frames.append(corrected_frame)
            input_hop = int(period * period_scale_factor)
            offset += input_hop

        n_randomized_phases = 50
        phases = np.exp(np.random.random((n_randomized_phases,)) * 2 * np.pi * 1j)

        output_hop = period * (expected_f0 / out_f0)

        result_length = int(len(frames) * output_hop) + len(frames[-1])
        result = np.zeros(result_length)
        for i, frame in enumerate(frames):
            frame = np.fft.rfft(frame)
            frame[:n_randomized_phases] = np.abs(frame[:n_randomized_phases]) * phases
            frame = np.fft.irfft(frame)
            frame = frame * scipy.signal.get_window("hann", len(frame))

            start = int(i * output_hop)
            end = int(i * output_hop) + len(frame)
            result[start:end] += frame

        return result

    def write_sample(self, pronunciation, out_file):
        for word in self.words:
            if word["pronunciation"] == pronunciation:
                start = self.beat_to_frame(word["start_beat"])
                end = self.beat_to_frame(word["end_beat"])
                audio = self.audio[start:end]
                audio = self.do_psola(audio)
                soundfile.write(out_file, audio, samplerate=self.rate)
                return
        else:
            raise RuntimeError(f"Pronunciation not found: {pronunciation}")

if __name__ == "__main__":

    database = DiphoneDatabase("STE-048.wav", "words.txt")
    database.write_sample(["h", "i", "r"], "out.wav")
