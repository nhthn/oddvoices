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

    def get_instantaneous_f0(self, signal, offset, window_size=2048):
        unwindowed_frame: np.array = signal[offset:offset + window_size]
        frame: np.array = unwindowed_frame * scipy.signal.get_window("hann", window_size)

        autocorrelation: np.array = scipy.signal.correlate(frame, frame)
        autocorrelation = autocorrelation[window_size:]
        ascending_bins = np.where(np.diff(autocorrelation) >= 0)
        if len(ascending_bins[0]) == 0:
            return -1
        first_ascending_bin = np.min(ascending_bins)
        measured_period: int = np.argmax(autocorrelation[first_ascending_bin:]) + first_ascending_bin
        measured_f0 = self.rate / measured_period
        return measured_f0

    def do_psola(self, segment, out_f0=200.0):
        expected_f0: float = 440 * 2 ** ((52 - 69) / 12)
        period: float = self.rate / expected_f0

        frames = []

        current_measured_period = period
        offset = 0
        while True:
            autocorrelation_window_size: int = 2048
            if offset + autocorrelation_window_size >= len(segment):
                break

            f0 = self.get_instantaneous_f0(
                segment, offset, window_size=autocorrelation_window_size
            )

            voiced = expected_f0 / 1.5 <= f0 <= expected_f0 * 1.5
            measured_period = self.rate / f0 if voiced else period
            window_size = int(measured_period * 2)

            unwindowed_frame: np.array = segment[offset:offset + window_size]
            frame: np.array = unwindowed_frame * scipy.signal.get_window("hann", window_size)
            corrected_frame: np.array = scipy.signal.resample(frame, int(period * 2))
            frames.append(corrected_frame)

            offset += int(measured_period)

        n_randomized_phases = 100
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

    def say_word(self, word):
        start = self.beat_to_frame(word["start_beat"])
        end = self.beat_to_frame(word["end_beat"])
        audio = self.audio[start:end]
        audio = self.do_psola(audio)
        return audio

    def write_sample(self, pronunciation_string, out_file):
        pronunciation = phonetics.parse_pronunciation(pronunciation_string)
        pronunciations = [[]]
        for phoneme in pronunciation:
            if phoneme == " ":
                pronunciations.append([])
            else:
                pronunciations[-1].append(phoneme)

        result = []
        for pronunciation in pronunciations:
            for word in self.words:
                if word["pronunciation"] == pronunciation:
                    result.append(self.say_word(word))
                    break
            else:
                raise RuntimeError(f"Pronunciation not found: {pronunciation}")
        audio = np.concatenate(result)
        soundfile.write(out_file, audio, samplerate=self.rate)

if __name__ == "__main__":

    database = DiphoneDatabase("STE-048.wav", "words.txt")
    database.write_sample("maI laIf Iz raIt j{}", "out.wav")
