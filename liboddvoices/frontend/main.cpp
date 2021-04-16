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
    for (auto& event : j["events"]) {
        float duration = event["duration"];
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

    for (int i : j["segments"]) {
        synth.queueSegment(i);
    }

    int t = 0;
    for (auto& event : j["events"]) {
        float duration = event["duration"];

        if (!event["frequency"].is_null()) {
            synth.setFrequency(event["frequency"]);
        }
        if (!event["formant_shift"].is_null()) {
            synth.setFormantShift(event["formant_shift"]);
        }
        if (!event["phoneme_speed"].is_null()) {
            synth.setPhonemeSpeed(event["phoneme_speed"]);
        }
        if (!event["note_on"].is_null() && event["note_on"]) {
            synth.noteOn();
        }
        if (!event["note_off"].is_null() && event["note_off"]) {
            synth.noteOff();
        }
        for (int j = 0; j < sampleRate * duration; j++) {
            samples[t] = synth.process() / 32768.0;
            t++;
        }
    }

    sf_write_float(soundFile, samples, numSamples);
    sf_close(soundFile);

    delete samples;

    return 0;
}
