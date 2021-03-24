import pytest

import oddvoices.g2p


def test_pronounce_text_basic():
    text = "hello world"
    expected = [
        ["_", "h", "@", "l"],
        ["oU", "_"],
        ["_", "w", "@`", "l", "d", "_"],
    ]
    assert oddvoices.g2p.pronounce_text(text) == expected


def test_pronounce_text_punctuation():
    text = "hello, world"
    expected = [
        ["_", "h", "@", "l"],
        ["oU", "_"],
        ["_", "w", "@`", "l", "d", "_"],
    ]
    assert oddvoices.g2p.pronounce_text(text) == expected


def test_pronounce_text_nonsense_word():
    text = "hallo worldo"
    expected = [
        ["_", "h", "{}", "l"],
        ["oU", "_"],
        ["_", "w", "oU", "r"],
        ["l", "d", "oU", "_"],
    ]
    assert oddvoices.g2p.pronounce_text(text) == expected


def test_pronounce_text_xsampa():
    text = "hello /w@`ld/"
    expected = [
        ["_", "h", "@", "l"],
        ["oU", "_"],
        ["_", "w", "@`", "l", "d", "_"],
    ]
    assert oddvoices.g2p.pronounce_text(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("hello world", ["hello", "world"]),
        ("hello, world!", ["hello", "world"]),
        (",hello !world", ["hello", "world"]),
        ("hello ,/w!rld/!", ["hello", "/w!rld/"]),
    ]
)
def test_split_words_and_strip_punctuation(text, expected):
    assert oddvoices.g2p.split_words_and_strip_punctuation(text) == expected


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
