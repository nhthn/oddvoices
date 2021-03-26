import pytest

import oddvoices.g2p


@pytest.fixture(scope="module")
def cmudict():
    return oddvoices.g2p.read_cmudict()


@pytest.mark.parametrize(
    "pronunciation, expected",
    [
        (["O", "t"], ["A", "t"]),
        (["f", "O", "r"], ["f", "oU", "r"]),
        (["f", "O"], ["f", "A"]),
    ]
)
def test_perform_cot_caught_merger(pronunciation, expected):
    oddvoices.g2p.perform_cot_caught_merger(pronunciation)
    assert pronunciation == expected


def test_pronounce_text_basic(cmudict):
    text = "hello world"
    expected = [
        "-", "_", "h", "@", "l",
        "-", "oU", "_",
        "-", "_", "w", "@`", "l", "d", "_",
    ]
    assert oddvoices.g2p.pronounce_text(text, cmudict) == expected


def test_pronounce_text_punctuation(cmudict):
    text = "hello, world"
    expected = [
        "-", "_", "h", "@", "l",
        "-", "oU", "_",
        "-", "_", "w", "@`", "l", "d", "_",
    ]
    assert oddvoices.g2p.pronounce_text(text, cmudict) == expected


def test_pronounce_text_nonsense_word(cmudict):
    text = "hallo worldo"
    expected = [
        "-", "_", "h", "{}", "l",
        "-", "oU", "_",
        "-", "_", "w", "oU", "r",
        "-", "l", "d", "oU", "_",
    ]
    assert oddvoices.g2p.pronounce_text(text, cmudict) == expected


def test_pronounce_text_xsampa(cmudict):
    text = "hello /w@`ld/"
    expected = [
        "-", "_", "h", "@", "l",
        "-", "oU", "_",
        "-", "_", "w", "@`", "l", "d", "_",
    ]
    assert oddvoices.g2p.pronounce_text(text, cmudict) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("hello world", ["hello", "world"]),
        ("Hello World", ["hello", "world"]),
        ("hello-world", ["hello", "world"]),
        ("hello, world!", ["hello", "world"]),
        (",hello !world", ["hello", "world"]),
        ("hello /w!rld/", ["hello", "/w!rld/"]),
        ("hello ,/w!rld/", ["hello", "w", "rld"]),
        ("world's", ["world's"]),
    ]
)
def test_tokenize(text, expected):
    assert oddvoices.g2p.tokenize(text) == expected


@pytest.mark.parametrize(
    "word, expected",
    [
        ("world", ["w", "oU", "r", "l", "d"]),
        ("greed", ["g", "r", "i", "d"]),
        ("summer", ["s", "@", "m", "@`"]),
    ]
)
def test_pronounce_unrecognized_word(word, expected):
    assert oddvoices.g2p.pronounce_unrecognized_word(word) == expected
