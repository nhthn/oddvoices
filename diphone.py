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


class Segment:

    def __init__(
        self,
        rate: float,
        in_f0: float,
        frames,
        out_f0: float,
        formant_shift: float = 1.0,
        duration=None
    ):
        self.rate: float = rate
        self.in_f0: float = in_f0
        self.out_f0: float = out_f0
        self.formant_shift: float = formant_shift
        self.original_frames = []
        for wavetable in frames:
            frame = Frame(self.rate, wavetable, self.out_f0, formant_shift=formant_shift)
            self.original_frames.append(frame)
        if len(self.original_frames) == 0:
            raise RuntimeError("Empty segment")

        self.duration: float
        if duration is None:
            self.duration = self.original_duration
        else:
            self.duration = duration

        period_count: int = int(self.duration * self.out_f0)
        self.frames = []
        for i in range(period_count):
            t = i / period_count
            frame = self.original_frames[int(t * len(self.original_frames))]
            self.frames.append(frame)

    @property
    def original_duration(self):
        return len(self.original_frames) / self.in_f0

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


    def say_segment(self, segment_name, f0=200.0, duration=None, formant_shift=1.0):
        if len(segment_name) == 1 and segment_name[0] in phonology.DIPHTHONGS:
            return (
                self.say_segment(
                    (segment_name[0], "stable"),
                    duration=duration,
                    f0=f0,
                    formant_shift=formant_shift,
                )
                + self.say_segment(
                    (segment_name[0], "transition"),
                    f0=f0,
                    formant_shift=formant_shift,
                )
            )
        info = self.segments[segment_name]
        start_frame = info["start_frame"]
        end_frame = info["end_frame"]
        segment = self.audio[start_frame:end_frame]

        frames = self.analyze_psola(segment)

        return [Segment(
            rate=self.rate,
            in_f0=self.expected_f0,
            frames=frames,
            out_f0=f0,
            duration=duration,
            formant_shift=formant_shift,
        )]

    def sing(self, music, out_file):
        out_segments = []

        psola_segments = []
        for note in music["notes"]:
            f0 = midi_note_to_hertz(note["midi_note"])

            phonemes = phonology.parse_pronunciation(note["phonemes"])
            phonemes = phonology.normalize_pronunciation(phonemes)

            vowel_count = sum([
                1 if phoneme in phonology.VOWELS else 0
                for phoneme in phonemes
            ])
            vowel_duration = note.get("duration", 1) / vowel_count
            vowel_duration *= music["time_scale"]

            for i in range(len(phonemes) - 1):
                diphone = (phonemes[i], phonemes[i + 1])
                if phonemes[i] in phonology.VOWELS:
                    segment = self.say_segment(
                        (phonemes[i],),
                        f0=f0,
                        duration=vowel_duration,
                        formant_shift=music["formant_shift"],
                    )
                    psola_segments.extend(segment)
                if diphone in self.segments:
                    segment = self.say_segment(
                        diphone,
                        f0=f0,
                        formant_shift=music["formant_shift"],
                    )
                    psola_segments.extend(segment)

        frames = []
        for segment in psola_segments:
            frames.extend(segment.frames)
        audio = synthesize_psola(frames)

        soundfile.write(out_file, audio, samplerate=self.rate)

if __name__ == "__main__":

    database = DiphoneDatabase(
        "STE-049.wav",
        "STE-049-labels.txt",
        expected_f0=midi_note_to_hertz(53),
    )
    music = {
        "time_scale": 0.3,
        "formant_shift": 1.1,
        "notes": [
            {"midi_note": 57, "phonemes": "meIr"},
            {"midi_note": 55, "phonemes": "ri"},
            {"midi_note": 53, "phonemes": "h{}d"},
            {"midi_note": 55, "phonemes": "@"},
            {"midi_note": 57, "phonemes": "lId"},
            {"midi_note": 57, "phonemes": "@l"},
            {"midi_note": 57, "phonemes": "l{}m", "duration": 2},
            {"midi_note": 55, "phonemes": "lId"},
            {"midi_note": 55, "phonemes": "@l"},
            {"midi_note": 55, "phonemes": "l{}m", "duration": 2},
            {"midi_note": 57, "phonemes": "lId"},
            {"midi_note": 60, "phonemes": "@l"},
            {"midi_note": 60, "phonemes": "l{}m", "duration": 2},
        ]
    }
    for note in music["notes"]:
        note["midi_note"] += 5
    database.sing(music, "out.wav")
