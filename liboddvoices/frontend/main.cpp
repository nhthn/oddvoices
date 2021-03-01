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

    int t = 0;
    for (auto& note : j["notes"]) {
        synth.setFrequency(note["frequency"]);

        synth.queueSegment(-1);
        for (auto& segment : note["segments"]) {
            int index = database->segmentToSegmentIndex(segment);
            synth.queueSegment(index);
        }

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
