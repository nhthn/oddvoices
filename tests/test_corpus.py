import numpy as np
import oddvoices.corpus

def test_write_and_read_voice_file():
    database = {
        "rate": 44100,
        "grain_length": 3,
        "phonemes": ["a", "b"],
        "segments_list": ["0", "1"],
        "segments": {
            "0": {
                "frames": np.array([[1, 2, 3], [-4, 5, 6]], dtype="int16"),
                "num_frames": 2,
                "offset": 0,
                "long": False
            },
            "1": {
                "frames": np.array([[-4, 5, 6]], dtype="int16"),
                "num_frames": 1,
                "offset": 0,
                "long": True
            },
        }
    }

    with open("file.voice", "wb") as f:
        oddvoices.corpus.write_voice_file(f, database)
    with open("file.voice", "rb") as f:
        result = oddvoices.corpus.read_voice_file(f)

    assert database["rate"] == result["rate"]
    assert database["grain_length"] == result["grain_length"]
    assert database["segments_list"] == result["segments_list"]
    assert database["phonemes"] == result["phonemes"]

    for segment_id in database["segments_list"]:
        expected = database["segments"][segment_id]
        actual = result["segments"][segment_id]
        assert expected["num_frames"] == actual["num_frames"]
        assert np.all(expected["frames"] == actual["frames"])
