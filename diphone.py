import soundfile
import scipy.signal
import numpy as np

import phonology

def get_sublist_index(list_1, list_2):
    for i in range(len(list_2) - len(list_1) + 1):
        if list(list_1) == list_2[i : i + len(list_1)]:
            return i
    raise IndexError("Sublist not found")


def midi_note_to_hertz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)


def seconds_to_timestamp(seconds):
    minutes = int(seconds / 60)
    remaining_seconds = seconds - minutes * 60
    return str(minutes) + ":" + str(remaining_seconds)


class DiphoneDatabase:

    def __init__(self, sound_file, label_file, expected_f0):
        self.expected_f0: float = expected_f0
        self.bpm: float = 60.0
        self.beat: float = 60 / self.bpm
        self.audio: np.array
        self.rate: int
        self.audio, self.rate = soundfile.read(sound_file)

        self.n_randomized_phases = 30
        self.randomized_phases = np.exp(np.random.random((self.n_randomized_phases,)) * 2 * np.pi * 1j)

        self.parse_label_file(label_file)

    def parse_label_file(self, label_file):
        self.segments = {}
        with open(label_file) as label_file:
            for line in label_file:
                entries = line.strip().split(maxsplit=2)
                if len(entries) == 3:
                    start, end, text = entries
                    start = float(start)
                    end = float(end)
                    text = text.split()
                    try:
                        text = tuple(phonology.parse_pronunciation(text[0]) + text[1:])
                    except RuntimeError as e:
                        print(seconds_to_timestamp(start))
                        raise e from None

                    self.segments[text] = {
                        "start_frame": int(float(start) * self.rate),
                        "end_frame": int(float(end) * self.rate),
                    }

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

    def crossfade_psola(self, frames_1, frames_2, nominal_crossfade_length):
        crossfade_length = min([len(frames_1), len(frames_2), nominal_crossfade_length])
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
        if len(frames) == 0:
            raise RuntimeError("Empty PSOLA")
        output_hop = self.rate / out_f0
        result_length = int(len(frames) * output_hop) + len(frames[-1])
        result = np.zeros(result_length)
        for i, frame in enumerate(frames):
            frame = scipy.signal.resample(frame, int(len(frame) / formant_shift))
            start = int(i * output_hop)
            end = int(i * output_hop) + len(frame)
            result[start:end] += frame
        return result

    def say_segment(self, segment_name):
        if len(segment_name) == 1 and segment_name[0] in phonology.DIPHTHONGS:
            return (
                self.say_segment((segment_name[0], "stable"))
                + self.say_segment((segment_name[0], "transition"))
            )
        info = self.segments[segment_name]
        start_frame = info["start_frame"]
        end_frame = info["end_frame"]
        segment = self.audio[start_frame:end_frame]
        return self.analyze_psola(segment)

    def sing(self, music, out_file):
        out_segments = []
        for note in music:
            f0 = midi_note_to_hertz(note["midi_note"])

            phonemes = phonology.parse_pronunciation(note["phonemes"])
            phonemes = phonology.normalize_pronunciation(phonemes)

            psola_segments = []
            for i in range(len(phonemes) - 1):
                diphone = (phonemes[i], phonemes[i + 1])
                if phonemes[i] in phonology.VOWELS:
                    psola_segments.append(self.say_segment((phonemes[i],)))
                if diphone in self.segments:
                    psola_segments.append(self.say_segment(diphone))

            merged_psola_segments = psola_segments[0]
            for psola_segment in psola_segments[1:]:
                merged_psola_segments = self.crossfade_psola(
                    merged_psola_segments, psola_segment, 20
                )
            out_segments.append(
                self.synthesize_psola(merged_psola_segments, out_f0=f0)
            )

        audio = np.concatenate(out_segments)

        soundfile.write(out_file, audio, samplerate=self.rate)

if __name__ == "__main__":

    database = DiphoneDatabase(
        "STE-049.wav",
        "STE-049-labels.txt",
        expected_f0=midi_note_to_hertz(53),
    )
    music = [
        {"midi_note": 57, "phonemes": "meIr"},
        {"midi_note": 55, "phonemes": "ri"},
        {"midi_note": 53, "phonemes": "h{}d"},
        {"midi_note": 55, "phonemes": "@"},
        {"midi_note": 57, "phonemes": "lId"},
        {"midi_note": 57, "phonemes": "@l"},
        {"midi_note": 57, "phonemes": "l{}m"},
        {"midi_note": 55, "phonemes": "lId"},
        {"midi_note": 55, "phonemes": "@l"},
        {"midi_note": 55, "phonemes": "l{}m"},
        {"midi_note": 57, "phonemes": "lId"},
        {"midi_note": 60, "phonemes": "@l"},
        {"midi_note": 60, "phonemes": "l{}m"},
    ]
    database.sing(music, "out.wav")
