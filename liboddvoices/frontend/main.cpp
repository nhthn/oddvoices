#include "json.hpp"
#include <sndfile.h>

#include "liboddvoices.hpp"

using json = nlohmann::json;

int main(int argc, char** argv)
{
    if (argc < 4) {
        std::cerr << "usage: liboddvoices_frontend VOICE_FILE IN_JSON OUT_WAV" << std::endl;
        return 1;
    }

    auto database = std::make_shared<oddvoices::Database>(argv[1]);
    float sampleRate = database->getSampleRate();
    oddvoices::Synth synth(sampleRate, database);

    json j;
    {
        std::ifstream ifstream(argv[2]);
        ifstream >> j;
    }

    float totalDuration = 0;
    for (auto& note : j["notes"]) {
        float duration = note["duration"];
        totalDuration += duration;
    }

    SF_INFO sf_info;
    sf_info.samplerate = sampleRate;
    sf_info.channels = 1;
    sf_info.format = SF_FORMAT_WAV | SF_FORMAT_PCM_16;
    sf_info.sections = 0;
    sf_info.seekable = 0;
    auto soundFile = sf_open(argv[3], SFM_WRITE, &sf_info);

    int numSamples = sampleRate * totalDuration;
    float* samples = new float[numSamples];

    for (unsigned int i = 0; i < j["phonemes"].size() - 1; i++) {
        auto syllableBreak = false;
        std::string phoneme1 = j["phonemes"][i];

        int phoneme1SegmentIndex = database->segmentToSegmentIndex(phoneme1);
        if (phoneme1SegmentIndex != -1) {
            synth.queueSegment(phoneme1SegmentIndex);
        }

        auto phoneme2Index = i + 1;
        std::string phoneme2 = j["phonemes"][phoneme2Index];
        while (phoneme2 == "-" && (i + 2 < j["phonemes"].size())) {
            syllableBreak = true;
            phoneme2Index += 1;
            phoneme2 = j["phonemes"][phoneme2Index];
        }
        auto segmentName = phoneme1 + phoneme2;
        auto segmentIndex = database->segmentToSegmentIndex(segmentName);
        if (segmentIndex != -1) {
            synth.queueSegment(segmentIndex);
        }
        if (syllableBreak) {
            synth.queueSegment(-1);
        }
    }

    int t = 0;
    for (auto& note : j["notes"]) {
        synth.setFrequency(note["frequency"]);

        float duration = note["duration"];
        float trim = note["trim"];
        synth.noteOn();
        for (int j = 0; j < sampleRate * (duration - trim); j++) {
            samples[t] = synth.process() / 32768.0;
            t++;
        }
        synth.noteOff();
        for (int j = 0; j < sampleRate * trim; j++) {
            samples[t] = synth.process() / 32768.0;
            t++;
        }
    }

    sf_write_float(soundFile, samples, numSamples);
    sf_close(soundFile);

    delete samples;

    return 0;
}
