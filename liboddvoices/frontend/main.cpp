#include "liboddvoices.hpp"
#include <sndfile.h>

int main(int argc, char** argv)
{
    SF_INFO sf_info;
    sf_info.samplerate = 48000;
    sf_info.channels = 1;
    sf_info.format = SF_FORMAT_WAV | SF_FORMAT_PCM_16;
    sf_info.sections = 1;
    sf_info.seekable = 0;
    auto soundFile = sf_open("out.wav", SFM_WRITE, &sf_info);

    float sampleRate = 48000;
    oddvoices::Synth synth(sampleRate, std::make_shared<oddvoices::Database>());

    int numSamples = sampleRate * 1;
    float* samples = new float[numSamples];
    for (int i = 0; i < numSamples; i++) {
        samples[i] = synth.process() / 32768.0;
    }

    sf_write_float(soundFile, samples, numSamples);
    sf_close(soundFile);

    delete samples;

    return 0;
}
