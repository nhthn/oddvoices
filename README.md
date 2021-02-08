## Using the synthesizer

Install [Git LFS](https://git-lfs.github.com/) and make sure you are up to date:

    git lfs init
    git lfs pull

Install Python dependencies:

    pip install soundfile numpy scipy

Run:

    python diphone.py music.json

Audio output is at `out.wav`.

## Database

`python phonology.py` yields a list of around 700 nonsense words that, when sung, produce a corpus of all possible diphones in General American English (GA). They are provided in random order to keep singers from getting too bored.

All pronunciations are provided using X-SAMPA notation. X-SAMPA is similar to IPA, but uses ASCII characters. One minor change is that /æ/ is represented with `{}` to prevent bracket matching issues in text editors. (The closing curly bracket represents /ʉ/, which is not found in GA.)

The word database was created manually. Many diphones are omitted because they are rare or nonexistent in English, such as `dZU` or `oIT`. Others are better represented as diphthongs, such as `Aj` becoming `aI`. A good number of diphone omissions are ad hoc decisions because I couldn't think of a common word.

## Recording a corpus

**Note: these instructions are incomplete/incorrect, do not attempt yet.**

In a quiet recording environment, record singing all words in order. I recommend using a pop filter if possible to prevent overly loud plosives. With 750 words and a few seconds each, you'll need to set aside about an hour total. To minimize fatigue, take breaks and record in multiple sessions.

All words should be sung in monotone. Pick a note in a comfortable register where you can safely avoid cracks, vocal fries, and other artifacts, and (importantly) keep that note fixed through the entire corpus. Minor pitch deviations within 50 cents or so are not likely to be a problem. It is fine to do multiple takes for a word.

Pay close attention to the X-SAMPA pronunciation. Some words, especially those with unstressed syllables, may have obvious spoken pronunciation but multiple ways to sing.

All vowels should be drawn out to a second or longer. In the case of diphthongs, delay the vowel transition to the end so there is an extended region with stable formants. These stable regions are critical for the singing synthesizer to sound good on long notes.

Consonants should be crisp and short compared to vowels. Anunciate clearly, but not unnaturally.

## Processing and tagging the corpus

If there are multiple audio files, concatenate them together into one big audio file. If there are multiple channels, take only one.

Open up the audio file in Audacity. (On Linux, be sure to use JACK and not ALSA or PulseAudio. Audacity lies about the endpoints during audio playback!)

