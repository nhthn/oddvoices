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

CONSONANTS = APPROXIMANTS + [
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
    "oU",
    "eI",
    "aI",
    "OI",
    "aU",
]

ALL_PHONEMES = CONSONANTS + APPROXIMANTS + VOWELS

IMPORTANT_DIPHONES = []
for vowel in VOWELS:
    for consonant in CONSONANTS:
        if consonant == "Z":
            continue
        if consonant != "h":
            IMPORTANT_DIPHONES.append((vowel, consonant))
        if consonant != "N":
            IMPORTANT_DIPHONES.append((consonant, vowel))

UNIMPORTANT_DIPHONES = [
    # nonsensical
    ("@", "r"),
    ("@r", "r"),
    ("r", "@r"),
    ("@r", "j"),
    ("j", "@r"),
    ("@r", "w"),
    ("oU", "w"),
    ("i", "j"),
    ("eI", "j"),
    ("aI", "j"),
    ("OI", "j"),
    ("aU", "w"),

    ("{}", "j"),
    ("{}", "r"),
    ("D", "A"),
    ("A", "j"),
    ("I", "r"),
    ("I", "j"),
    ("I", "w"),
    ("E", "j"),
    ("E", "w"),

    # Probably don't exist in English
    ("@", "j"),  # usually becomes aI
    ("u", "N"),
    ("U", "N"),
    ("@r", "N"),
    ("i", "N"),
    ("oU", "N"),
    ("eI", "N"),
    ("aI", "N"),

    # Rare
    ("u", "dZ"),  # nothing rhymes with "splooge"

    # U + approximant usually becomes u or @
    ("U", "l"),
    ("U", "r"),
    ("U", "w"),
    ("U", "j"),

    # Can't think of any:
    ("T", "E"),
    ("E", "N"),
    ("T", "u"),
    ("D", "u"),
    ("j", "U"),
    ("U", "m"),
    ("U", "n"),
    ("U", "p"),
    ("U", "b"),
    ("tS", "U"),
    ("U", "dZ"),
    ("dZ", "U"),
    ("f", "U"),
    ("U", "f"),
    ("v", "U"),
    ("U", "T"),
    ("T", "U"),
    ("U", "D"),
    ("D", "U"),
    ("U", "s"),
    ("s", "U"),
    ("U", "z"),
    ("z", "U"),
    ("U", "v"),
    ("i", "b"),
    ("i", "dZ"),
    ("oU", "dZ"),
    ("oU", "j"),
    ("eI", "S"),
    ("j", "aI"),
    ("aI", "w"),
    ("aI", "g"),
    ("aI", "tS"),
    ("@r", "D"),  # very rare except "merther"
    ("aI", "dZ"),
    ("aI", "T"),
    ("z", "aI"), # Zybourne Clock?
    ("aI", "S"),
]
for diphone in UNIMPORTANT_DIPHONES:
    IMPORTANT_DIPHONES.remove(diphone)

def parse_words(file):
    words = []
    for line in file:
        line = line.strip()
        if line == "":
            continue
        word, __, pronunciation = line.partition("=")
        word = word.strip()
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
        vowel_count = 0
        for phoneme in phonemes:
            if phoneme in VOWELS:
                vowel_count += 1
        words.append({
            "word": word,
            "pronunciation": phonemes,
            "vowel_count": vowel_count,
        })
    return words

def check_words(words):
    missing = 0
    found = 0
    for diphone in IMPORTANT_DIPHONES:
        for word in words:
            if is_sublist(diphone, word["pronunciation"]):
                found += 1
                break
        else:
            missing += 1
            if missing <= 10:
                print(diphone)
    if missing != 0:
        raise RuntimeError(f"{missing} out of {len(IMPORTANT_DIPHONES)} diphones missing")

if __name__ == "__main__":
    with open("words2.txt") as f:
        words = parse_words(f)
        check_words(words)
