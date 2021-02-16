import logging
import json
import pathlib

import soundfile
import scipy.signal
import numpy as np

import phonology

def get_sublist_index(list_1, list_2):
    for i in range(len(list_2) - len(list_1) + 1):
        if list(list_1) == list_2[i : i + len(list_1)]:
            return i
    raise IndexError("Sublist not found")


def hertz_to_midi_note(hertz):
    return np.log2(hertz / 440) * 12 + 69


def midi_note_to_hertz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)


def seconds_to_timestamp(seconds):
    minutes = int(seconds / 60)
    remaining_seconds = seconds - minutes * 60
    return str(minutes) + ":" + str(remaining_seconds)


class Frame:

    def __init__(self, rate, wavetable, f0, formant_shift=1.0):
        self.rate = rate
        self.wavetable = wavetable
        self.f0 = f0
        self.formant_shift = formant_shift

    @property
    def hop_size(self):
        return self.rate / self.f0

    def __len__(self):
        return len(self.wavetable)

    @property
    def formant_shifted_wavetable_length(self):
        return int(len(self.wavetable) / self.formant_shift)

    @property
    def formant_shifted_wavetable(self):
        return scipy.signal.resample(self.wavetable, self.formant_shifted_wavetable_length)

    def crossfade(self, other, t):
        return Frame(
            rate=self.rate,
            wavetable=self.wavetable * (1 - t) + other.wavetable * t,
            f0=self.f0,
            formant_shift=self.formant_shift,
        )


class Segment:

    def __init__(
        self,
        name,
        rate: float,
        in_f0: float,
        frames,
        out_f0: float,
        original_duration: float,
        formant_shift: float = 1.0,
        duration=None
    ):
        self.name = name
        self.rate: float = rate
        self.in_f0: float = in_f0
        self.out_f0: float = out_f0
        self.formant_shift: float = formant_shift
        self.original_frames = []
        for i in range(frames.shape[0]):
            frame = Frame(self.rate, frames[i, :], self.out_f0, formant_shift=formant_shift)
            self.original_frames.append(frame)
        if len(self.original_frames) == 0:
            raise RuntimeError("Empty segment")

        self.original_duration = original_duration

        self.duration: float
        if duration is None:
            self.duration = self.original_duration
        else:
            self.duration = duration

    def compute_frames(self):
        period_count: int = int(self.duration * self.out_f0)
        self.frames = []
        for i in range(period_count):
            frame = self.original_frames[int(i * self.in_f0 / self.out_f0) % len(self.original_frames)]
            self.frames.append(frame)

    def crossfade(self, other, duration=0.03):
        average_f0 = np.sqrt(self.out_f0 * other.out_f0)
        nominal_crossfade_length = int(duration * average_f0)
        crossfade_length = min([len(self.frames), len(other.frames), nominal_crossfade_length])
        crossfade_frames = []
        for i in range(crossfade_length):
            t = i / crossfade_length
            frame_1 = self.frames[-crossfade_length + i]
            frame_2 = other.frames[i]
            crossfade_frames.append(frame_1.crossfade(frame_2, t))
        crossfade_1 = crossfade_frames[:crossfade_length // 2]
        crossfade_2 = crossfade_frames[crossfade_length // 2:]
        for frame in crossfade_1:
            frame.f0 = self.out_f0
            frame.formant_shfit = self.formant_shift
        for frame in crossfade_2:
            frame.f0 = other.out_f0
            frame.formant_shfit = other.formant_shift
        self.frames = self.frames[:-crossfade_length] + crossfade_1
        other.frames = crossfade_2 + other.frames[crossfade_length:]


def synthesize_psola(frames):
    result_length = sum([frame.hop_size for frame in frames])
    result_length += len(frames[0]) // 2
    result_length += len(frames[-1]) // 2
    result_length = int(result_length)
    result = np.zeros(result_length)
    position = 0
    for i, frame in enumerate(frames):
        hop = frame.hop_size
        wavetable = frame.formant_shifted_wavetable
        start = int(position)
        end = start + len(wavetable)
        result[start:end] += wavetable
        position += hop
    return result


def smooth_f0(frames):
    f0_midi_note = hertz_to_midi_note(frames[0].f0)
    for frame in frames:
        hop_in_seconds = frame.hop_size / frame.rate
        k = 1 - (hop_in_seconds * 40)
        f0_midi_note = hertz_to_midi_note(frame.f0) * (1 - k) + f0_midi_note * k
        frame.f0 = midi_note_to_hertz(f0_midi_note)


class CorpusAnalyzer:

    def __init__(self, directory):
        root = pathlib.Path(directory)
        sound_file = root / "audio.wav"
        label_file = root / "labels.txt"
        info_file = root / "database.json"

        with open(info_file) as f:
            info = json.load(f)

        self.expected_f0: float = midi_note_to_hertz(info["f0_midi_note"])
        self.audio: np.array
        self.rate: int
        self.audio, self.rate = soundfile.read(sound_file)

        self.n_randomized_phases = 30
        self.randomized_phases = np.exp(np.random.random((self.n_randomized_phases,)) * 2 * np.pi * 1j)

        self.parse_label_file(label_file)

    def parse_label_file(self, label_file):
        self.markers = {}
        with open(label_file) as label_file:
            for line in label_file:
                entries = line.strip().split(maxsplit=2)
                if len(entries) == 3:
                    start, end, text = entries
                    start = float(start)
                    end = float(end)
                    segment_id = tuple(phonology.parse_pronunciation(text))

                    self.markers[segment_id] = {
                        "start": int(float(start) * self.rate),
                        "end": int(float(end) * self.rate),
                    }

    def get_audio_between_markers(self, markers):
        start_frame = markers["start"]
        end_frame = markers["end"]
        return self.audio[start_frame:end_frame]

    def render_database(self):
        self.database = {"rate": self.rate, "expected_f0": self.expected_f0}
        for segment_id in sorted(list(self.markers.keys())):
            print(segment_id)
            markers = self.markers[segment_id]
            segment = self.get_audio_between_markers(markers)
            frames = self.analyze_psola(segment)
            self.database["".join(segment_id)] = np.array(frames)
            self.database["".join(segment_id) + "_original_duration"] = len(frames) / self.expected_f0
        return self.database

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



class DiphoneSynth:

    def __init__(self, database):
        self.rate = database["rate"]
        self.expected_f0 = database["expected_f0"]
        self.database = database

    def say_segment(self, segment_id, f0=200.0, duration=None, formant_shift=1.0):
        return Segment(
            name=segment_id,
            rate=self.rate,
            in_f0=self.expected_f0,
            frames=self.database["".join(segment_id)],
            out_f0=f0,
            duration=duration,
            original_duration=self.database["".join(segment_id) + "_original_duration"],
            formant_shift=formant_shift,
        )

    def sing(self, music, out_file):
        out_segments = []
        psola_segments = []

        for note in music["notes"]:
            syllable_segments = []
            f0 = midi_note_to_hertz(note["midi_note"] + music["transpose"])

            phonemes = phonology.normalize_pronunciation(note["phonemes"])

            vowel_count = sum([
                1 if phoneme in phonology.VOWELS else 0
                for phoneme in phonemes
            ])

            for i in range(len(phonemes) - 1):
                diphone = (phonemes[i], phonemes[i + 1])
                if phonemes[i] in phonology.VOWELS:
                    segment = self.say_segment(
                        (phonemes[i],),
                        f0=f0,
                        formant_shift=music["formant_shift"],
                    )
                    syllable_segments.append(segment)
                if "".join(diphone) in self.database:
                    segment = self.say_segment(
                        diphone,
                        f0=f0,
                        formant_shift=music["formant_shift"],
                    )
                    syllable_segments.append(segment)

            diphones_duration = 0
            for segment in syllable_segments:
                if len(segment.name) == 2:
                    diphones_duration += segment.duration
            total_duration = note.get("duration", 1)
            vowels_duration = total_duration - diphones_duration
            vowel_duration = vowels_duration / vowel_count

            for segment in syllable_segments:
                if len(segment.name) == 1:
                    segment.duration = vowel_duration

            psola_segments.extend(syllable_segments)

        for segment in psola_segments:
            segment.compute_frames()

        for i in range(len(psola_segments) - 1):
            psola_segments[i].crossfade(psola_segments[i + 1])

        frames = []
        for segment in psola_segments:
            frames.extend(segment.frames)
        smooth_f0(frames)
        audio = synthesize_psola(frames)

        soundfile.write(out_file, audio, samplerate=self.rate)

if __name__ == "__main__":
    segment_database = CorpusAnalyzer("nwh").render_database()
    np.savez("segments.npz", **segment_database)
