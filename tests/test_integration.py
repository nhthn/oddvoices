import json
import pathlib
import subprocess
import tempfile

import numpy as np
import scipy.signal
import soundfile
import pytest

import oddvoices.synth
import oddvoices.corpus
import common


CPP_EXECUTABLE = common.TEST_ROOT.parent / "liboddvoices/build/liboddvoices_frontend"

EXAMPLE_VOICE = common.TEST_ROOT / "compiled-voices/quake.voice"

EXAMPLE_MUSIC_BASIC = {
    "segments": [-1, 0, 1, 2, -1, 3, 4, 5, -1, 6, 7, 8],
    "notes": [
        {"frequency": 100, "duration": 2, "trim": 0.2},
        {"frequency": 150, "duration": 2, "trim": 0.25},
        {"frequency": 200, "duration": 2, "trim": 0.5},
    ],
}

EXAMPLE_MUSIC_PHONEME_SPEED = {
    "segments": [-1, 0, 1, 2, -1, 3, 4, 5, -1, 6, 7, 8],
    "notes": [
        {"frequency": 100, "duration": 2, "trim": 0.2, "phoneme_speed": 2},
        {"frequency": 150, "duration": 2, "trim": 0.25, "phoneme_speed": 1},
        {"frequency": 200, "duration": 2, "trim": 0.5, "phoneme_speed": 0.5},
    ],
}

EXAMPLE_MUSIC_FORMANT_SHIFT = {
    "segments": [-1, 0, 1, 2, -1, 3, 4, 5, -1, 6, 7, 8],
    "notes": [
        {"frequency": 100, "duration": 2, "trim": 0.2, "formant_shift": 2},
        {"frequency": 150, "duration": 2, "trim": 0.25, "formant_shift": 1},
        {"frequency": 200, "duration": 2, "trim": 0.5, "formant_shift": 0.5},
    ],
}


def spectrogram(signal):
    return np.abs(scipy.signal.stft(signal)[2])


@pytest.mark.parametrize(
    "music, tolerance",
    [
        (EXAMPLE_MUSIC_BASIC, 0.09),
        (EXAMPLE_MUSIC_PHONEME_SPEED, 0.09),
        (EXAMPLE_MUSIC_FORMANT_SHIFT, 0.13),
    ],
)
def test_cpp_vs_python(music, tolerance):
    music_json = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
    json.dump(music, music_json)
    music_json.seek(0)

    out_wav = tempfile.NamedTemporaryFile(mode="w+")

    subprocess.run(
        [CPP_EXECUTABLE, EXAMPLE_VOICE, music_json.name, out_wav.name], check=True
    )
    result_cpp, rate = soundfile.read(out_wav.name)

    with open(EXAMPLE_VOICE, "rb") as f:
        database = oddvoices.corpus.read_voice_file(f)
    synth = oddvoices.synth.Synth(database)
    result_py = oddvoices.synth.sing(synth, music)

    assert rate == int(synth.sample_rate)
    np.testing.assert_allclose(
        spectrogram(result_cpp), spectrogram(result_py), rtol=0, atol=tolerance
    )


def test_sample_rates():
    with open(EXAMPLE_VOICE, "rb") as f:
        database = oddvoices.corpus.read_voice_file(f)

    sample_rate_1 = 48000
    synth_1 = oddvoices.synth.Synth(database, sample_rate=sample_rate_1)
    result_1 = oddvoices.synth.sing(synth_1, EXAMPLE_MUSIC_BASIC)

    sample_rate_2 = 8000
    synth_2 = oddvoices.synth.Synth(database, sample_rate=sample_rate_2)
    result_2 = oddvoices.synth.sing(synth_2, EXAMPLE_MUSIC_BASIC)

    np.testing.assert_almost_equal(
        len(result_1) / sample_rate_1, len(result_2) / sample_rate_2
    )

    result_1 = scipy.signal.resample(result_1, len(result_2))

    np.testing.assert_allclose(
        spectrogram(result_1), spectrogram(result_2), rtol=0, atol=0.02
    )
