## Using the synthesizer

Install [Git LFS](https://git-lfs.github.com/) and make sure you are up to date:

    git lfs init
    git lfs pull

Install Python dependencies:

    pip install soundfile numpy scipy

Run:

    python frontend.py music.json

Audio output is at `out.wav`.

## Corpus

The corpus was created manually in the file `words.txt`, which spans most common CV and CC diphones in General American English (GA).

All pronunciations are provided using X-SAMPA notation. X-SAMPA is similar to IPA, but uses ASCII characters. One minor change is that /æ/ is represented with `{}` to prevent bracket matching issues in text editors. (The closing curly bracket represents /ʉ/, which is not found in GA.)

## Recording a corpus

In a quiet recording environment, record all words in `words.pdf` in order. I recommend using a pop filter if possible to prevent overly loud plosives. With 1100 words and a few seconds each, you'll need to set aside 1-2 hours. To minimize fatigue, take breaks and record in multiple sessions.

All words should be sung in monotone. Pick a note in a comfortable register where you can safely avoid cracks, vocal fries, and other artifacts, and (importantly) keep that note fixed through the entire corpus. Minor pitch deviations within 50 cents or so are not likely to be a problem. It is fine to do multiple takes for a word.

## Processing and tagging the corpus

If there are multiple audio files, concatenate them together into one big audio file. If there are multiple channels, take only one to ensure a mono audio file.

Open up the audio file in Audacity. (On Linux, be sure to use JACK and not ALSA or PulseAudio. Audacity lies about the endpoints during audio playback!) For each word, tag all diphones indicated by the light gray text.
