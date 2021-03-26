from typing import Dict, List
import string
import sys

import oddvoices.phonology
import oddvoices.utils


def arpabet_to_xsampa(string: str) -> str:
    """Convert an ARPABET phoneme string to X-SAMPA."""
    if string[-1].isdigit():
        return oddvoices.phonology.ARPABET_TO_XSAMPA[string[:-1]]
    return oddvoices.phonology.ARPABET_TO_XSAMPA[string]


def read_cmudict() -> Dict[str, List[str]]:
    """Parse the packaged cmudict file and return a Python dictionary mapping
    lowercase words to X-SAMPA pronunciations. Examples:

    {
        "hello": ["h", "@", "l", "oU"],
        "and": ["{}", "n", "d"],
        ...
    }
    """
    pronunciation_dict = {}
    with open(oddvoices.utils.BASE_DIR / "cmudict-0.7b", encoding="windows-1252") as f:
        for line in f:
            if line.startswith(";;;"):
                continue
            parts = line.split()
            pronunciation_dict[parts[0].lower()] = [arpabet_to_xsampa(x) for x in parts[1:]]
    pronunciation_dict.update(oddvoices.phonology.CMUDICT_EXCEPTIONS)
    return pronunciation_dict


def split_syllables(phonemes: List[str]) -> List[str]:
    """Given an X-SAMPA pronunciation of a word, prepend a "-" phoneme to each syllable."""
    return _SyllableSplitter(phonemes)()


class _SyllableSplitter:

    def __init__(self, phonemes):
        self.phonemes = phonemes
        self.syllables = []
        self.new_syllable()

    def new_syllable(self):
        self.current_syllable_has_vowel: bool = False
        self.current_syllable: List[str] = []
        self.syllables.append(self.current_syllable)

    def __call__(self) -> List[str]:
        for phoneme in self.phonemes:
            if phoneme in oddvoices.phonology.VOWELS:
                if self.current_syllable_has_vowel:
                    self.new_syllable()
                self.current_syllable_has_vowel = True
            else:
                if self.current_syllable_has_vowel and self.current_syllable[-1] in oddvoices.phonology.CONSONANTS:
                    self.new_syllable()
            self.current_syllable.append(phoneme)

        if not self.current_syllable_has_vowel and len(self.syllables) > 1:
            self.syllables[-2].extend(self.syllables.pop())

        result = []
        for syllable in self.syllables:
            result.append("-")
            result.extend(syllable)

        return result


def tokenize(text: str) -> List[str]:
    """Split a text into words and remove punctuation."""
    islands = text.split()
    words = []

    punctuation = ".!,;:\"'()[]-"
    for island in islands:
        if island.startswith("/"):
            new_word = island
            while new_word[-1] in punctuation:
                new_word = new_word[:-1]
            if not new_word.endswith("/"):
                raise RuntimeError(f"Syntax error: {new_word}")
            words.append(new_word)
        else:
            new_word_characters: List[str] = []
            lower_island: str = island.lower()
            for character in lower_island:
                if character not in string.ascii_lowercase + "'":
                    if len(new_word_characters) != 0:
                        words.append("".join(new_word_characters))
                        new_word_characters = []
                else:
                    new_word_characters.append(character)
            if len(new_word_characters) != 0:
                words.append("".join(new_word_characters))

    return words


def pronounce_unrecognized_word(word: str) -> List[str]:
    """Guess an X-SAMPA pronunciation of an unrecognized or OOV (out-of-vocabulary)
    word."""
    phonemes = []
    keys = sorted(
        list(oddvoices.phonology.GUESS_PRONUNCIATIONS.keys()),
        key=len,
        reverse=True,
    )

    remaining_word = word + "$"
    while len(remaining_word) != 0:
        for key in keys:
            if remaining_word.startswith(key):
                remaining_word = remaining_word[len(key):]
                new_phonemes = oddvoices.phonology.GUESS_PRONUNCIATIONS[key]
                if isinstance(new_phonemes, list):
                    phonemes.extend(new_phonemes)
                else:
                    phonemes.append(new_phonemes)
                break
        else:
            remaining_word = remaining_word[1:]

    phonemes_pass_2 = []
    last_phoneme = None
    for phoneme in phonemes:
        if phoneme != last_phoneme:
            phonemes_pass_2.append(phoneme)
        last_phoneme = phoneme

    phonemes = phonemes_pass_2
    return phonemes


def perform_cot_caught_merger(pronunciation: List[str]) -> None:
    for i, phoneme in enumerate(pronunciation):
        if phoneme == "O":
            if i + 1 < len(pronunciation) and pronunciation[i + 1] == "r":
                pronunciation[i] = "oU"
            else:
                pronunciation[i] = "A"


def pronounce_word(word: str, pronunciation_dict: Dict[str, List[str]]) -> List[str]:
    if word.startswith("/"):
        return oddvoices.phonology.parse_pronunciation(word[1:-1])
    try:
        pronunciation = pronunciation_dict[word.lower()]
        perform_cot_caught_merger(pronunciation)
    except KeyError:
        pronunciation = pronounce_unrecognized_word(word)
    return pronunciation


def pronounce_text(text: str, pronunciation_dict: Dict[str, List[str]]) -> List[List[str]]:
    """Convert an entire text into a list of syllables pronounced with X-SAMPA."""
    words = tokenize(text)

    syllables = []
    for word in words:
        pronunciation = pronounce_word(word, pronunciation_dict)
        pronunciation = oddvoices.phonology.normalize_pronunciation(pronunciation)
        syllables.extend(split_syllables(pronunciation))

    return syllables


def main():
    text = " ".join(sys.argv[1:])

    cmudict = read_cmudict()
    phonemes = pronounce_text(text, cmudict)
    print(" ".join(phonemes))
