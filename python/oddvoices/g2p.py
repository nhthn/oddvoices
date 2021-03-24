import oddvoices.phonology
import oddvoices.utils
from typing import Dict, List


def arpabet_to_xsampa(string: str) -> str:
    """Convert an ARPABET phoneme string to X-SAMPA."""
    if string[-1].isdigit():
        return oddvoices.phonology.ARPABET_TO_XSAMPA[string[:-1]]
    return oddvoices.phonology.ARPABET_TO_XSAMPA[string]


def read_cmu_dict() -> Dict[str, List[str]]:
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
            line = line.split()
            pronunciation_dict[line[0].lower()] = [arpabet_to_xsampa(x) for x in line[1:]]
    pronunciation_dict.update(oddvoices.phonology.CMUDICT_EXCEPTIONS)
    return pronunciation_dict


def split_syllables(word: List[str]) -> List[List[str]]:
    """Given an X-SAMPA pronunciation of a word, split it into syllables."""
    result = []
    current_syllable = None
    current_syllable_has_vowel = False
    def new_syllable():
        nonlocal current_syllable
        nonlocal current_syllable_has_vowel
        current_syllable_has_vowel = False
        current_syllable = []
        result.append(current_syllable)
    new_syllable()
    for phoneme in word:
        if phoneme in oddvoices.phonology.VOWELS:
            if current_syllable_has_vowel:
                new_syllable()
            current_syllable_has_vowel = True
        else:
            if current_syllable_has_vowel and current_syllable[-1] in oddvoices.phonology.CONSONANTS:
                new_syllable()
        current_syllable.append(phoneme)

    if not current_syllable_has_vowel and len(result) > 1:
        result[-2].extend(result.pop())

    return result


def split_words_and_strip_punctuation(text: str) -> List[str]:
    """Split a text into words and remove all punctuation."""
    words_pass_1 = text.split()
    words_pass_2 = []

    punctuation = ".!,;:\"'()[]-"
    for word in words_pass_1:
        if word.startswith("/"):
            new_word = word
            while new_word[-1] in punctuation:
                new_word = new_word[:-1]
            if not new_word.endswith("/"):
                raise RuntimeError(f"Syntax error: {new_word}")
            words_pass_2.append(new_word)
        else:
            new_word = word
            while len(new_word) != 0 and new_word[-1] in punctuation:
                new_word = new_word[:-1]
            while len(new_word) != 0 and new_word[0] in punctuation:
                new_word = new_word[1:]
            if len(new_word) != 0:
                words_pass_2.append(new_word)

    words = words_pass_2
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

    while len(word) != 0:
        for key in keys:
            if word.startswith(key):
                word = word[len(key):]
                new_phonemes = oddvoices.phonology.GUESS_PRONUNCIATIONS[key]
                if isinstance(new_phonemes, list):
                    phonemes.extend(new_phonemes)
                else:
                    phonemes.append(new_phonemes)
                break
        else:
            word = word[1:]

    phonemes_pass_2 = []
    last_phoneme = None
    for phoneme in phonemes:
        if phoneme != last_phoneme:
            phonemes_pass_2.append(phoneme)
        last_phoneme = phoneme

    phonemes = phonemes_pass_2
    return phonemes


def pronounce_text(text: str) -> List[List[str]]:
    """Convert an entire text into a list of syllables pronounced with X-SAMPA."""
    words = split_words_and_strip_punctuation(text)

    pronunciation_dict = read_cmu_dict()
    syllables = []
    for word in words:
        if word.startswith("/"):
            pronunciation = oddvoices.phonology.parse_pronunciation(word[1:-1])
        else:
            try:
                pronunciation = pronunciation_dict[word.lower()]
            except KeyError:
                pronunciation = pronounce_unrecognized_word(word)
        pronunciation = oddvoices.phonology.normalize_pronunciation(pronunciation)
        syllables.extend(split_syllables(pronunciation))

    return syllables
