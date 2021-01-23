## Database

`words2_shuffled.txt` is a list of around 350 English words (and a few non-words) that, when sung, produce a corpus of most of the common vowel-consonant and consonant-vowel diphones in General American English (GA). They are provided in random order to keep singers from getting too bored.

All pronunciations are provided using X-SAMPA notation. X-SAMPA is similar to IPA, but uses ASCII characters. One minor change is that /æ/ is represented with `{}` to prevent bracket matching issues in text editors. (The closing curly bracket represents /ʉ/, which is not found in GA.)

The word database was created manually. Many diphones are omitted because they are rare or nonexistent in English, such as `dZU` or `oIT`. Others are better represented as diphthongs, such as `Aj` becoming `aI`. A good number of diphone omissions are ad hoc decisions because I couldn't think of a common word.

## Recording a corpus

In a quiet recording environment, record singing all words in order. I recommend using a pop filter if possible to prevent overly loud plosives. With 350 words and a few seconds each, you'll need to set aside 20-30 minutes total. To minimize fatigue, take breaks and record in multiple sessions.

All words should be sung in monotone. Pick a note in a comfortable register where you can safely avoid cracks, vocal fries, and other artifacts, and (importantly) keep that note fixed through the entire corpus. Minor pitch deviations within 50 cents or so are not likely to be a problem. It is fine to do multiple takes for a word.

Pay close attention to the X-SAMPA pronunciation. Some words, especially those with unstressed syllables, may have obvious spoken pronunciation but multiple ways to sing.

All vowels should be drawn out to a second or longer. In the case of diphthongs, delay the vowel transition to the end so there is an extended region with stable formants. These stable regions are critical for the singing synthesizer to sound good on long notes.

Consonants should be crisp and short compared to vowels. Anunciate clearly, but not unnaturally.

## Processing and tagging the corpus

If there are multiple audio files, concatenate them together into one big audio file. If there are multiple channels, take only one.

Open up the audio file in Audacity. (On Linux, be sure to use JACK and not ALSA or PulseAudio. Audacity lies about the endpoints during audio playback!)

The first three steps involve tagging individual phonemes. The stable regions of vowels and diphthongs are used for held notes when singing. The final step is the most laborious, involving tagging hundreds of diphones.

Step 1. For each of the nine vowels, locate a stable region and tag it.

Step 2. For each of the five diphthongs, tag its stable region as (e.g.) `eI stable` and its transition region as `eI transition`.

Step 3. For each of the 20 consonants, find a segment and tag it.

Step 4. Tag all CV and VC diphones. Remember that the glottal stop `?` counts as a consonant!
