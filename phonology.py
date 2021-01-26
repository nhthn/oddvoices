import random
import subprocess


def is_sublist(list_1, list_2):
    for i in range(len(list_2) - len(list_1) + 1):
        if list(list_1) == list_2[i : i + len(list_1)]:
            return True
    return False

APPROXIMANTS = [
    "l",
    "r",
    "j",
    "w",
]

NON_APPROXIMANT_CONSONANTS = [
    "m",
    "n",
    "N",
    "h",
    "k",
    "g",
    "p",
    "b",
    "t",
    "d",
    "tS",
    "dZ",
    "f",
    "v",
    "T",
    "D",
    "s",
    "z",
    "S",
    "Z",
]

CONSONANTS = APPROXIMANTS + NON_APPROXIMANT_CONSONANTS

DIPHTHONGS = [
    "oU",
    "eI",
    "aI",
    "OI",
    "aU",
]

VOWELS = [
    "{}",
    "A",
    "I",
    "E",
    "@",
    "u",
    "U",
    "@r",
    "i",
] + DIPHTHONGS

SPECIAL = ["_"]

ALL_PHONEMES = CONSONANTS + VOWELS + SPECIAL


def parse_pronunciation(pronunciation):
    pronunciation = pronunciation.strip()
    phonemes = []
    while len(pronunciation) != 0:
        for phoneme in sorted(ALL_PHONEMES, key=lambda x: len(x), reverse=True):
            if pronunciation.startswith(phoneme):
                phonemes.append(phoneme)
                pronunciation = pronunciation[len(phoneme):]
                break
        else:
            raise RuntimeError(f"Unrecognized phoneme: {pronunciation}")
    return phonemes

def generate_word_list():
    word_list = []
    for i, phoneme_1 in enumerate(ALL_PHONEMES):
        for phoneme_2 in ALL_PHONEMES[i + 1:]:
            type_: str
            pair: tuple(str, str)
            if phoneme_1 in CONSONANTS and phoneme_2 in VOWELS:
                type_ = "cv"
                pair = phoneme_1, phoneme_2
            elif phoneme_2 in CONSONANTS and phoneme_1 in VOWELS:
                type_ = "cv"
                pair = phoneme_2, phoneme_1
            elif phoneme_1 in CONSONANTS and phoneme_2 in CONSONANTS:
                type_ = "cc"
                pair = phoneme_1, phoneme_2
            elif phoneme_1 in VOWELS and phoneme_2 in VOWELS:
                type_ = "vv"
                pair = phoneme_1, phoneme_2
            elif "_" in (phoneme_1, phoneme_2):
                if phoneme_1 == "_":
                    pair = phoneme_2, phoneme_1
                else:
                    pair = phoneme_1, phoneme_2
                if phoneme_1 in VOWELS:
                    type_ = "_v"
                elif phoneme_1 in CONSONANTS:
                    type_ = "_c"

            if type_ == "cv":
                word_list.append(["t", "A", pair[0], pair[1], pair[0], "A"])
            elif type_ == "cc":
                word_list.append(["t", "A", pair[0], pair[1], "A"])
            elif type_ == "vv":
                word_list.append(["t", pair[0], pair[1]])
            elif type_ == "_v":
                word_list.append([pair[0], "t", "A", "t", pair[0]])
            elif type_ == "_c":
                word_list.append([pair[0], "A", pair[0]])

    return word_list

if __name__ == "__main__":
    word_list = generate_word_list()
    random.shuffle(word_list)
    for word in word_list:
        print("".join(word))
    print(len(word_list), "words")
