import json
import pathlib
import soundfile
import scipy.signal
import numpy as np
import oddvoices.phonology

def midi_note_to_hertz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)

def seconds_to_timestamp(seconds):
    minutes = int(seconds / 60)
    remaining_seconds = seconds - minutes * 60
    return str(minutes) + ":" + str(remaining_seconds)


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
                    segment_id = tuple(oddvoices.phonology.parse_pronunciation(text))

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
            markers = self.markers[segment_id]
            segment = self.get_audio_between_markers(markers)
            frames = self.analyze_psola(segment)
            if len(segment_id) == 1 and segment_id[0] in oddvoices.phonology.VOWELS:
                frames = self.make_loopable(frames)
            self.database["".join(segment_id)] = frames
            self.database["".join(segment_id) + "_original_duration"] = len(frames) / self.expected_f0
        self.normalize_database()
        return self.database

    def normalize_database(self):
        max_ = 0
        for segment_id in sorted(list(self.markers.keys())):
            max_ = max(max_, np.max(np.abs(self.database["".join(segment_id)])))
        for segment_id in sorted(list(self.markers.keys())):
            name = "".join(segment_id)
            self.database[name] = self.database[name] * 32767 / max_
            self.database[name] = self.database[name].astype(np.int16)

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
                frame[0] = 0
                frame = np.fft.irfft(frame)
                frame = frame * scipy.signal.get_window("hann", len(frame))
            if len(frame) < int(period * 2):
                frame = np.concatenate([frame, np.zeros(int(period * 2) - len(frame))])
            frames.append(frame)
            offset += int(measured_period)
        if len(frames) == 0:
            raise RuntimeError("Zero frames")
        return np.array(frames)

    def make_loopable(self, frames):
        n_old = frames.shape[0]
        if n_old % 2 == 1:
            n_old -= 1
        n_new = n_old // 2
        t = np.linspace(0, 1, n_new, endpoint=False)
        return (
            frames[:n_new, :] * t[:, np.newaxis]
            + frames[n_new:n_old, :] * (1 - t[:, np.newaxis])
        )


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("in_dir")
    parser.add_argument("out_file")
    args = parser.parse_args()

    segment_database = CorpusAnalyzer(args.in_dir).render_database()
    np.savez_compressed(args.out_file, **segment_database)
