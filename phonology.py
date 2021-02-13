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
    "@`",
    "i",
] + DIPHTHONGS

SPECIAL = ["_"]

ALL_PHONEMES = CONSONANTS + VOWELS + SPECIAL

XSAMPA_TO_IPA = {
    "{}": "æ",
    "A": "ɑ",
    "I": "ɪ",
    "E": "ɛ",
    "@": "ə",
    "U": "ʊ",
    "@`": "ɚ",
    "i": "i",
    "N": "ŋ",
    "tS": "tʃ",
    "dZ": "dʒ",
    "T": "θ",
    "D": "ð",
    "S": "ʃ",
    "Z": "ʒ",
    "oU": "oʊ",
    "eI": "eɪ",
    "aI": "aɪ",
    "OI": "ɔɪ",
    "aU": "aʊ",
}

def as_ipa_string(tokens):
    result = []
    for phoneme in tokens:
        if phoneme in XSAMPA_TO_IPA:
            result.append(XSAMPA_TO_IPA[phoneme])
        else:
            result.append(phoneme)
    return "/" + "".join(result) + "/"

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
            if pronunciation[0] == "?":
                phonemes.append("_")
                pronunciation = pronunciation[1:]
            else:
                raise RuntimeError(f"Unrecognized phoneme: {pronunciation}")
    return phonemes

def normalize_pronunciation(pronunciation):
    if pronunciation[0] != "_":
        pronunciation = ["_"] + pronunciation
    if pronunciation[-1] != "_":
        pronunciation = pronunciation + ["_"]
    return pronunciation

def generate_nonsense_word_list():
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
                word_list.append({
                    "word": ["t", "A", pair[0], pair[1], pair[0], "A"],
                    "segments": [
                        [pair[0], pair[1]],
                        [pair[1], pair[0]],
                    ]
                })
            elif type_ == "cc" and pair[0] != "h":
                word_list.append({
                    "word": ["t", "A", pair[0], pair[1], "A"],
                    "segments": [[pair[0], pair[1]]],
                })
                word_list.append({
                    "word": ["t", "A", pair[1], pair[0], "A"],
                    "segments": [[pair[1], pair[0]]],
                })
            elif type_ == "vv":
                word_list.append({
                    "word": ["t", pair[0], pair[1]],
                    "segments": [[pair[0], pair[1]]],
                })
                word_list.append({
                    "word": ["t", pair[1], pair[0]],
                    "segments": [[pair[1], pair[0]]],
                })
            elif type_ == "_v":
                word_list.append({
                    "word": [pair[0], "t", "A", "t", pair[0]],
                    "segments": [
                        ["_", pair[0]],
                        [pair[0], "_"],
                    ],
                })
                word_list.append({
                    "word": [pair[0]],
                    "segments": [[pair[0]]],
                })
            elif type_ == "_c":
                word_list.append({
                    "word": [pair[0], "A", pair[0]],
                    "segments": [
                        ["_", pair[0]],
                        [pair[0], "_"],
                    ],
                })

    return word_list


def generate_base():
    for phoneme_1 in sorted(ALL_PHONEMES):
        for phoneme_2 in sorted(ALL_PHONEMES):
            if phoneme_1 != phoneme_2:
                print(phoneme_1 + phoneme_2)

def parse_wordlist(f):
    orphaned_diphones = []
    for line in f:
        line, __, __ = line.partition("#")
        line = line.strip()
        if line == "":
            continue
        parts = line.strip().split(maxsplit=2)
        diphones = [parse_pronunciation(part) for part in parts[0].split(",")]
        if len(parts) == 1:
            orphaned_diphones.extend(diphones)
        elif len(parts) == 3:
            pronunciation = line[1]
            text = line[2]
        else:
            raise RuntimeError(f"Parse error: {line}")

if __name__ == "__main__":

    with open("words.txt") as f:
        parse_wordlist(f)

    #word_list = generate_nonsense_word_list()
    #random.shuffle(word_list)
    #for word in word_list:
    #    print(as_ipa_string(word["word"]))
    #print(len(word_list), "words")
