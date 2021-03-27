import json
import pathlib
import subprocess
import tempfile

import numpy as np
import scipy.signal
import soundfile

import oddvoices.synth

import common


CPP_EXECUTABLE = common.TEST_ROOT.parent / "liboddvoices/build/liboddvoices_frontend"

EXAMPLE_VOICE = common.TEST_ROOT / "compiled-voices/quake.voice"

EXAMPLE_MUSIC = {
    "segments": [-1, 0, 1, 2, -1, 3, 4, 5, -1, 6, 7, 8],
    "notes": [
        {"frequency": 100, "duration": 2, "trim": 0.2},
        {"frequency": 150, "duration": 2, "trim": 0.25},
        {"frequency": 200, "duration": 2, "trim": 0.5},
    ],
}


def spectrogram(signal):
    return np.abs(scipy.signal.stft(signal)[2])


def test_cpp_vs_python():
    music_json = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
    json.dump(EXAMPLE_MUSIC, music_json)
    music_json.seek(0)

    out_wav = tempfile.NamedTemporaryFile(mode="w+")

    subprocess.run(
        [CPP_EXECUTABLE, EXAMPLE_VOICE, music_json.name, out_wav.name], check=True
    )
    result_cpp, rate = soundfile.read(out_wav.name)

    with open(EXAMPLE_VOICE, "rb") as f:
        database = oddvoices.corpus.read_voice_file(f)
    synth = oddvoices.synth.Synth(database)
    result_py = oddvoices.synth.sing(synth, EXAMPLE_MUSIC)

    assert rate == int(synth.rate)
    np.testing.assert_allclose(
        spectrogram(result_cpp), spectrogram(result_py), rtol=0, atol=0.09
    )


def test_sample_rates():
    with open(EXAMPLE_VOICE, "rb") as f:
        database = oddvoices.corpus.read_voice_file(f)

    synth_1 = oddvoices.synth.Synth(database, sample_rate=48000)
    result_1 = oddvoices.synth.sing(synth_1, EXAMPLE_MUSIC)

    synth_2 = oddvoices.synth.Synth(database, sample_rate=44100)
    result_2 = oddvoices.synth.sing(synth_2, EXAMPLE_MUSIC)
    result_2 = scipy.signal.resample(result_2, len(result_1))

    np.testing.assert_allclose(
        spectrogram(result_1), spectrogram(result_2), rtol=0, atol=0.09
    )
