import soundfile
import scipy.signal
import numpy as np

import phonology

def get_sublist_index(list_1, list_2):
    for i in range(len(list_2) - len(list_1) + 1):
        if list(list_1) == list_2[i : i + len(list_1)]:
            return i
    raise IndexError("Sublist not found")

class DiphoneDatabase:

    def __init__(self, sound_file, words_file):
        self.expected_f0: float = 440 * 2 ** ((52 - 69) / 12)
        self.bpm: float = 60.0
        self.beat: float = 60 / self.bpm
        self.audio: np.array
        self.rate: int
        self.audio, self.rate = soundfile.read(sound_file)
        self.audio = np.sum(self.audio, axis=1)

        self.n_randomized_phases = 30
        self.randomized_phases = np.exp(np.random.random((self.n_randomized_phases,)) * 2 * np.pi * 1j)

        with open(words_file) as f:
            self.words = phonology.parse_words(f)

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

        self.build_diphone_index()

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

    def build_diphone_index(self):
        self.diphones = {}
        for word in self.words:
            pronunciation = word["pronunciation"]
            start_beat = word["start_beat"]
            for i in range(len(pronunciation) - 1):
                phoneme_1 = pronunciation[i]
                phoneme_2 = pronunciation[i + 1]
                if phoneme_1 in phonology.VOWELS or phoneme_2 in phonology.VOWELS:
                    diphone = (phoneme_1, phoneme_2)
                    spec = {
                        "start_beat": start_beat,
                        "end_beat": start_beat + 1,
                    }
                    self.diphones[diphone] = spec
                    start_beat += 1

    def analyze_psola(self, segment):
        autocorrelation_window_size: int = 2048
        period: float = self.rate / self.expected_f0
        frames = []
        offset = 0

        while offset + autocorrelation_window_size < len(segment):

            f0 = self.get_instantaneous_f0(
                segment, offset, window_size=autocorrelation_window_size
            )

            voiced = self.expected_f0 / 1.5 <= f0 <= self.expected_f0 * 1.5
            measured_period = self.rate / f0 if voiced else period
            window_size = int(measured_period * 2)

            frame: np.array = segment[offset:offset + window_size]
            frame = frame * scipy.signal.get_window("hann", len(frame))
            frame = scipy.signal.resample(frame, int(period * 2))

            if voiced:
                frame = np.fft.rfft(frame)
                frame[:self.n_randomized_phases] = (
                    np.abs(frame[:self.n_randomized_phases]) * self.randomized_phases
                )
                frame = np.fft.irfft(frame)
                frame = frame * scipy.signal.get_window("hann", len(frame))

            if len(frame) < int(period * 2):
                frame = np.concatenate([frame, np.zeros(int(period * 2) - len(frame))])

            frames.append(frame)

            offset += int(measured_period)

        return frames

    def crossfade_psola(self, frames_1, frames_2, crossfade_length):
        result = []
        for frame in frames_1[:-crossfade_length]:
            result.append(frame)
        for i in range(crossfade_length):
            t = i / crossfade_length
            frame_1 = frames_1[-crossfade_length + i]
            frame_2 = frames_2[i]
            result.append(frame_1 * (1 - t) + frame_2 * t)
        for frame in frames_2[crossfade_length:]:
            result.append(frame)
        return result


    def synthesize_psola(self, frames, out_f0=200.0, formant_shift=1.0):
        output_hop = self.rate / out_f0
        result_length = int(len(frames) * output_hop) + len(frames[-1])
        result = np.zeros(result_length)
        for i, frame in enumerate(frames):
            frame = scipy.signal.resample(frame, int(len(frame) / formant_shift))
            start = int(i * output_hop)
            end = int(i * output_hop) + len(frame)
            result[start:end] += frame
        return result

    def say_word(self, word):
        start = self.beat_to_frame(word["start_beat"])
        end = self.beat_to_frame(word["end_beat"])
        audio = self.audio[start:end]
        audio = self.analyze_psola(audio)
        return audio

    def write_sample(self, pronunciation_string, out_file):
        pronunciation = phonology.parse_pronunciation(pronunciation_string)
        pronunciations = [[]]
        for phoneme in pronunciation:
            if phoneme == " ":
                pronunciations.append([])
            else:
                pronunciations[-1].append(phoneme)

        pronunciations = [
            phonology.normalize_pronunciation(pronunciation)
            for pronunciation in pronunciations
        ]

        psola_segments = []
        for pronunciation in pronunciations:
            for i in range(len(pronunciation) - 1):
                diphone = (pronunciation[i], pronunciation[i + 1])
                if diphone in self.diphones:
                    psola_segments.append(self.say_word(self.diphones[diphone]))

        merged_psola_segments = psola_segments[0]
        for psola_segment in psola_segments[1:]:
            merged_psola_segments = self.crossfade_psola(
                merged_psola_segments, psola_segment, 10
            )
        audio = self.synthesize_psola(merged_psola_segments)

        soundfile.write(out_file, audio, samplerate=self.rate)

if __name__ == "__main__":

    database = DiphoneDatabase("STE-048.wav", "words.txt")
    database.write_sample("tunaIt", "out.wav")
