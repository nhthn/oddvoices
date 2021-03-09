# OddVoices

**OddVoices** is a project to create open-source singing synths inspired by retro speech synthesis algorithms. The goal is to create interesting voices for use in experimental music. Expect quirky and unusual voices, and not necessarily intelligible ones.

Currently, OddVoices consists of two PSOLA-based singing synthesizers for General American English:

- nt, a deep, dark basso profondo
- nwh, a synthesizer-like baritone (barely intelligible)

## Roadmap

- Basic prototype in Python (done)
- C++ port (in progress)
- SuperCollider UGen
- Standalone C++ app
- VST plugin

## Using the synthesizer

Install [Git LFS](https://git-lfs.github.com/) and make sure you are up to date:

    git lfs pull

Set up Python virtualenv:

    python -m venv .venv
    source .venv/bin/activate
    pip install -e .

Analyze segments in `voices/nt` directory and generate the database file at `nt.voice`. You only need to do this once:

    oddvoices-compile voices/nt nt.voice

Sing the JSON file at `example/music.json`:

    sing nt.voice example/music.json out.wav

Sing a MIDI file (experimental, very rudimentary right now):

    sing-midi nt.voice example/example.mid -l "This is just a test of singing" out.wav

### Building and using the C++ synthesizer

The C++ synthesizer in the `liboddvoices` directory is a port of the Python synthesizer.

    cd liboddvoices
    mkdir build && cd build
    cmake ..

    liboddvoices_frontend ../../nwh.voice ../example/music.json out.wav

## Corpus

The corpus was created manually in the file `words.txt`, which spans most common CV and CC diphones in General American English (GA).

All pronunciations are provided using X-SAMPA notation. X-SAMPA is similar to IPA, but uses ASCII characters. One minor change is that /æ/ is represented with `{}` to prevent bracket matching issues in text editors. (The closing curly bracket represents /ʉ/, which is not found in GA.)

## Recording a corpus

In a quiet recording environment, record all words in `words.pdf` in order. I recommend using a pop filter if possible to prevent overly loud plosives. With 700 words and a few seconds each, you'll need to set aside about half an hour. To minimize fatigue, take breaks and record in multiple sessions.

All words should be sung in monotone without vibrato. Pick a note in a comfortable register where you can safely avoid cracks, vocal fries, and other artifacts, and keep that note fixed through the entire corpus. Poor intonation is not a big deal, but keep within 50 cents of the target frequency. It is fine to do multiple takes for a word.

Sing at a moderate pace and anunciate consonants well.

Any word tagged "(long)" is an isolated vowel. Make these a few seconds long. For diphthongs, always sing with a long stable region and a short transition at the end. For example, the diphone `aU` should sound like a long "aah" followed by a short "ow."

## Processing and tagging the corpus

If there are multiple audio files, concatenate them together into one big audio file. If there are multiple channels, take only one to ensure a mono audio file.

Open up the audio file in Audacity. (On Linux, be sure to use JACK and not ALSA or PulseAudio. Audacity lies about the endpoints during audio playback!) For each word, use Audacity's built-in labeling system tag the diphone(s) and vowels indicated by the light gray text.

For diphones, err on the side of longer: it is better for intelligibility to tag a little too long than a little too short. For vowels, tag only the stable region of diphthongs.

Tagging a 30-minute corpus takes about two hours of work.
