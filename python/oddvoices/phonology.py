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
    "@`",
    "A",
    "I",
    "E",
    "@",
    "u",
    "U",
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

ARPABET_TO_XSAMPA = {
    "AA": "A",
    "AE": "{}",
    "AH": "@",
    "AO": "A",
    "AW": "aU",
    "AY": "aI",
    "B": "b",
    "CH": "tS",
    "D": "d",
    "DH": "D",
    "EH": "E",
    "ER": "@`",
    "EY": "eI",
    "F": "f",
    "G": "g",
    "HH": "h",
    "IH": "I",
    "IY": "i",
    "JH": "dZ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "N",
    "OW": "oU",
    "OY": "OI",
    "P": "p",
    "R": "r",
    "S": "s",
    "SH": "S",
    "T": "t",
    "TH": "T",
    "UH": "U",
    "UW": "u",
    "V": "v",
    "W": "w",
    "Y": "j",
    "Z": "z",
    "ZH": "Z",
}


GUESS_PRONUNCIATIONS = {
    "a": "{}",
    "ai": "aI",
    "au": "aU",
    "b": "b",
    "c": "k",
    "ch": "tS",
    "d": "d",
    "e": "E",
    "ei": "eI",
    "ee": "i",
    "ea": "i",
    "er": "@`",
    "f": "f",
    "g": "g",
    "h": "h",
    "i": "I",
    "ie": "aI",
    "j": "dZ",
    "k": "k",
    "l": "l",
    "m": "m",
    "n": "n",
    "ng": "N",
    "o": "oU",
    "oo": "u",
    "ou": "aU",
    "ow": "aU",
    "p": "p",
    "q": ["k", "w"],
    "r": "r",
    "s": "s",
    "sh": "S",
    "t": "t",
    "th": "T",
    "u": "@",
    "v": "v",
    "w": "w",
    "x": ["k", "s"],
    "y": "j",
    "z": "z",
}

CMUDICT_EXCEPTIONS = {
    "and": ["{}", "n", "d"],
    "for": ["f", "oU", "r"],
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


def generate_base():
    for phoneme_1 in sorted(ALL_PHONEMES):
        for phoneme_2 in sorted(ALL_PHONEMES):
            if phoneme_1 != phoneme_2:
                print(phoneme_1 + phoneme_2)


def parse_wordlist(f):
    wordlist = []
    for line in f:
        line, __, __ = line.partition("#")
        line = line.strip()
        if line == "":
            continue
        parts = line.strip().split(maxsplit=2)
        diphones = [parse_pronunciation(part) for part in parts[0].split(",")]
        if len(parts) != 3:
            raise RuntimeError(f"Parse error: {line}")
        pronunciation = parse_pronunciation(parts[1][1:-1])
        normalized_pronunciation = normalize_pronunciation(pronunciation)
        text = parts[2]
        for diphone in diphones:
            if not is_sublist(diphone, normalized_pronunciation):
                raise RuntimeError(f"{diphone} is not in {pronunciation}")
        wordlist.append({
            "diphones": diphones,
            "pronunciation": pronunciation,
            "text": text,
        })
    return wordlist



def generate_latex(words):
    result = []
    result.append(r"\documentclass{article}")
    result.append(r"\usepackage{fontspec}")
    result.append(r"\setmainfont{Doulos SIL}")
    result.append(r"\usepackage{setspace}")
    result.append(r"\usepackage{multicol}")
    result.append(r"\usepackage{xcolor}")
    result.append(r"\setlength{\columnsep}{1cm}")
    result.append(r"""
    \usepackage[
      margin=1.5cm,
      includefoot,
      footskip=30pt,
    ]{geometry}
    \usepackage{layout}
    """)

    result.append(r"\begin{document}")
    result.append(r"\singlespacing")
    result.append(r"\begin{multicols}{3}")
    result.append(r"\begin{enumerate}")
    result.append(r"""
        \setlength{\itemsep}{0pt}
        \setlength{\parskip}{0pt}
        \setlength{\parsep}{0pt}
    """)

    for word in words:
        pronunciation = as_ipa_string(word["pronunciation"])

        diphone_info = []
        for diphone in word["diphones"]:
            diphone_info.append("".join(diphone))
        diphone_info = ",".join(diphone_info)
        diphone_info = r"{\color{lightgray} \verb/" + diphone_info + r"/}"
        result.append(r"\item " + word["text"] + " " + pronunciation + " " + diphone_info)
        result.append("")

    result.append(r"\end{enumerate}")
    result.append(r"\end{multicols}")
    result.append(r"\end{document}")
    return result


def generate_wordlist():
    with open("words.txt") as f:
        wordlist = parse_wordlist(f)

    random.seed(0)
    random.shuffle(wordlist)
    with open("words.tex", "w") as f:
        latex = generate_latex(wordlist)
        for line in latex:
            f.write(line + "\n")

    subprocess.run(["xelatex", "words.tex"])
