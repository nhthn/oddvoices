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


def escape_latex(string):
    escaped_string = string
    escaped_string = escaped_string.replace("{", r"\{")
    escaped_string = escaped_string.replace("}", r"\}")
    escaped_string = escaped_string.replace("_", r"\_")
    return escaped_string


def generate_latex(words):
    result = []
    result.append(r"\documentclass{article}")
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
        diphone_info = []
        for diphone in word["diphones"]:
            diphone_info.append("".join(diphone))
        diphone_info = ",".join(diphone_info)
        diphone_info = escape_latex(diphone_info)
        diphone_info = f"{{\\color{{lightgray}} {diphone_info}}}"
        result.append(r"\item " + word["text"] + " " + diphone_info)
        result.append("")

    result.append(r"\end{enumerate}")
    result.append(r"\end{multicols}")
    result.append(r"\end{document}")
    return result



if __name__ == "__main__":

    with open("words.txt") as f:
        wordlist = parse_wordlist(f)

    random.seed(0)
    random.shuffle(wordlist)
    with open("words.tex", "w") as f:
        latex = generate_latex(wordlist)
        for line in latex:
            f.write(line + "\n")

    subprocess.run(["pdflatex", "words.tex"])
