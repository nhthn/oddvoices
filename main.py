from builtins import float

import numpy as np  # type: ignore
import scipy.signal  # type: ignore
import soundfile  # type: ignore
from typing import Tuple, List, Union


class VocalSegment:

    def __init__(self):
        self.frames = []

    def append(self, frame) -> None:
        self.frames.append(frame)

    def render(self) -> np.array:
        return np.concatenate([frame.render() for frame in self.frames])

    def merge_frames(self):
        new_frames = []
        current_type = None
        unvoiced_frames = []
        for frame in self.frames:
            if frame.type_ != current_type and len(unvoiced_frames) != 0:
                new_frames.append(VocalFrame.merge(unvoiced_frames))
                unvoiced_frames = []
                current_type = frame.type_
            if frame.type_ != "voiced":
                unvoiced_frames.append(frame)
            else:
                new_frames.append(frame)
        self.frames = new_frames

    def identify_silences(self):
        peak_amplitudes: np.array = np.array([frame.get_peak_amplitude() for frame in self.frames])
        median_amplitude = np.median(peak_amplitudes)
        silence_indices = np.where(peak_amplitudes < median_amplitude * 0.2)[0]
        for index in silence_indices:
            frame: VocalFrame = self.frames[index]
            frame.type_ = "silence"
            frame.run_length = len(frame.wavetable)
            frame.wavetable = np.array([0])


class VocalFrame:

    def __init__(self, type_: str, wavetable: np.array):
        assert type_ in ["voiced", "unvoiced", "silence"]
        if np.max(np.abs(wavetable)) > 1:
            wavetable = wavetable / np.max(np.abs(wavetable))
        self.type_ = type_
        self.wavetable = wavetable

    @classmethod
    def merge(cls, frames):
        frame_types = {frame.type_ for frame in frames}
        if len(frame_types) != 1:
            raise ValueError(f"Cannot merge frames of types {frame_types}")
        type_ = list(frame_types)[0]
        wavetable = np.concatenate([frame.render() for frame in frames])
        return cls(type_, wavetable)

    def limit(self) -> None:
        peak_amplitude: np.float = self.get_peak_amplitude()
        if peak_amplitude > 1:
            self.wavetable /= peak_amplitude

    def normalize(self) -> None:
        self.wavetable /= self.get_peak_amplitude()

    def get_peak_amplitude(self) -> np.float:
        return np.max(np.abs(self.wavetable))

    def get_spectrum(self):
        if self.type_ != "voiced":
            return
        log_magnitude_spectrum = 20 * np.log10(np.abs(np.fft.rfft(self.wavetable)[1:]))
        freq = np.fft.rfftfreq(len(self.wavetable), d=1 / 48000)[1:]
        log_freq = np.log2(freq)
        A = np.vstack([log_freq, np.ones(len(log_magnitude_spectrum))]).T
        slope, gain = np.linalg.lstsq(A, log_magnitude_spectrum, rcond=None)[0]
        linear_approximation = gain + slope * log_freq
        residual = log_magnitude_spectrum - linear_approximation

        import matplotlib.pyplot as plt
        plt.semilogx()
        plt.plot(freq, residual)
        plt.show()


    def render(self) -> np.array:
        return self.wavetable


if __name__ == "__main__":

    audio: np.array
    rate: int
    audio, rate = soundfile.read("STE-047.wav")

    audio = np.sum(audio, axis=1)

    segments: List[Tuple[float, float, str]] = []
    with open("labels.txt") as label_file:
        for line in label_file:
            start_str: str
            end_str: str
            label: str
            start_str, end_str, label = line.split(maxsplit=3)
            start: float = float(start_str)
            end: float = float(end_str)
            segments.append((start, end, label))

    out_signals = []

    for start, end, label in segments:
        vocal_frames: VocalSegment = VocalSegment()

        start_samples: int = int(start * rate)
        end_samples: int = int(end * rate)
        segment: np.array = audio[start_samples:end_samples]

        expected_f0 = 100.0
        expected_period: int = int(round(rate / expected_f0))
        periods_per_window: int = 5
        window_size: int = expected_period * periods_per_window

        length: int = end_samples - start_samples

        for offset in range(0, length - window_size, expected_period):
            unwindowed_frame: np.array = segment[offset:offset + window_size]
            backup_vocal_frame: VocalFrame = VocalFrame("unvoiced", segment[offset:offset + expected_period])
            frame: np.array = unwindowed_frame * scipy.signal.get_window("hann", window_size)
            autocorrelation: np.array = scipy.signal.correlate(frame, frame)
            autocorrelation = autocorrelation[window_size:]

            ascending_bins = np.where(np.diff(autocorrelation) >= 0)
            if len(ascending_bins[0]) == 0:
                vocal_frames.append(backup_vocal_frame)
                continue
            first_ascending_bin = np.min(ascending_bins)
            period: int = np.argmax(autocorrelation[first_ascending_bin:]) + first_ascending_bin
            f0 = rate / period

            if 0.5 < f0 / expected_f0 < 1.5:
                cropped_frame: np.array = unwindowed_frame[:int(window_size * expected_f0 / f0)]
                corrected_frame: np.array = scipy.signal.resample(cropped_frame, window_size)
                vocal_frame = VocalFrame("voiced", corrected_frame[:expected_period])
                vocal_frames.append(vocal_frame)
            else:
                vocal_frames.append(backup_vocal_frame)

        vocal_frames.identify_silences()
        vocal_frames.merge_frames()

        for vocal_frame in vocal_frames.frames:
            if vocal_frame.type_ == "voiced":
                vocal_frame.get_spectrum()
                break

        out_signals.append(vocal_frames.render())

    out_signal = np.concatenate(out_signals)
    soundfile.write("out.wav", out_signal, samplerate=rate)
