import json
import pathlib
import struct
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

    def normalize_database(self):
        max_ = 0
        for segment_id in sorted(list(self.markers.keys())):
            name = "".join(segment_id)
            max_ = max(max_, np.max(np.abs(self.database["segments"][name]["frames"])))
        for segment_id in sorted(list(self.markers.keys())):
            name = "".join(segment_id)
            self.database["segments"][name]["frames"] = self.database["segments"][name]["frames"] * 32767 / max_
            self.database["segments"][name]["frames"] = self.database["segments"][name]["frames"].astype(np.int16)

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

    def render_database(self):
        self.database = {
            "rate": self.rate,
            "phonemes": oddvoices.phonology.ALL_PHONEMES,
            "grain_length": 2 * int(self.rate / self.expected_f0),
            "segments_list": ["".join(x) for x in sorted(list(self.markers.keys()))],
            "segments": {},
        }

        for segment_id in sorted(list(self.markers.keys())):
            markers = self.markers[segment_id]
            segment = self.get_audio_between_markers(markers)
            frames = self.analyze_psola(segment)
            is_long = len(segment_id) == 1 and segment_id[0] in oddvoices.phonology.VOWELS
            if is_long:
                frames = self.make_loopable(frames)
            self.database["segments"]["".join(segment_id)] = {
                "frames": frames,
                "num_frames": len(frames),
                "long": is_long,
            }
        self.normalize_database()
        return self.database

MAGIC_WORD = b"ODDVOICES\0\0\0"

def write_voice_file_header(f, database):
    f.write(MAGIC_WORD)
    f.write(struct.pack("<l", database["rate"]))
    f.write(struct.pack("<l", database["grain_length"]))

    for phoneme in database["phonemes"]:
        f.write(phoneme.encode("ascii") + b"\0")
    f.write(b"\0")

    for segment_name in database["segments_list"]:
        f.write(segment_name.encode("ascii") + b"\0")
        num_frames = database["segments"][segment_name]["num_frames"]
        is_long = database["segments"][segment_name]["long"]
        f.write(struct.pack("<l", num_frames))
        f.write(struct.pack("<l", 1 if is_long else 0))
    f.write(b"\0")


def write_voice_file(f, database):
    write_voice_file_header(f, database)
    for segment_name in database["segments_list"]:
        array = database["segments"][segment_name]["frames"].flatten()
        packed_array = struct.pack(f"<{len(array)}h", *array)
        f.write(packed_array)


def read_string(f):
    result = []
    while True:
        c = f.read(1)
        if c == b"\0":
            break
        if len(result) > 255:
            raise ValueError("String longer than 255 characters")
        result.append(c)
    return b"".join(result).decode("ascii")


def read_voice_file_header(f, database):
    if f.read(len(MAGIC_WORD)) != MAGIC_WORD:
        raise RuntimeError("Invalid voice file")
    database["rate"] = struct.unpack("<l", f.read(4))[0]
    database["grain_length"] = struct.unpack("<l", f.read(4))[0]

    database["phonemes"] = []
    while True:
        phoneme = read_string(f)
        if len(phoneme) == 0:
            break
        database["phonemes"].append(phoneme)

    database["segments_list"] = []
    database["segments"] = {}
    while True:
        segment_id = read_string(f)
        if len(segment_id) == 0:
            break
        database["segments_list"].append(segment_id)
        database["segments"][segment_id] = {}
        database["segments"][segment_id]["num_frames"] = struct.unpack("<l", f.read(4))[0]
        database["segments"][segment_id]["long"] = struct.unpack("<l", f.read(4))[0] != 0


def read_voice_file(f):
    database = {}
    read_voice_file_header(f, database)

    for segment_id in database["segments_list"]:
        num_frames = database["segments"][segment_id]["num_frames"]
        num_samples = num_frames * database["grain_length"]
        array = np.array(struct.unpack(f"<{num_samples}h", f.read(num_samples * 2)))
        array = array.reshape(num_frames, database["grain_length"])
        database["segments"][segment_id]["frames"] = array

    return database


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("in_dir")
    parser.add_argument("out_file")
    args = parser.parse_args()

    segment_database = CorpusAnalyzer(args.in_dir).render_database()

    with open(args.out_file, "wb") as f:
        write_voice_file(f, segment_database)
