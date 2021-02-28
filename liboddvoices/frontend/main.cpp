#include "liboddvoices.hpp"
#include <sndfile.h>

int main(int argc, char** argv)
{
    auto database = std::make_shared<oddvoices::Database>("nwh.voice");
    float sampleRate = database->getSampleRate();
    oddvoices::Synth synth(sampleRate, database);

    SF_INFO sf_info;
    sf_info.samplerate = sampleRate;
    sf_info.channels = 1;
    sf_info.format = SF_FORMAT_WAV | SF_FORMAT_PCM_16;
    sf_info.sections = 0;
    sf_info.seekable = 0;
    auto soundFile = sf_open("out.wav", SFM_WRITE, &sf_info);

    synth.setFrequency(150);
    synth.queueSegment(database->segmentToSegmentIndex("_h"));
    synth.queueSegment(database->segmentToSegmentIndex("hE"));
    synth.queueSegment(database->segmentToSegmentIndex("E"));
    synth.queueSegment(database->segmentToSegmentIndex("El"));
    synth.queueSegment(-1);
    synth.queueSegment(database->segmentToSegmentIndex("loU"));
    synth.queueSegment(database->segmentToSegmentIndex("oU"));
    synth.queueSegment(database->segmentToSegmentIndex("oU_"));
    synth.noteOn();

    int numSamples = sampleRate * 4.0;
    float* samples = new float[numSamples];

    int i = 0;
    for (; i < sampleRate * 0.9; i++) {
        samples[i] = synth.process() / 32768.0;
    }
    synth.noteOff();
    for (; i < sampleRate * 1.0; i++) {
        samples[i] = synth.process() / 32768.0;
    }
    synth.noteOn();
    for (; i < sampleRate * 2.0; i++) {
        samples[i] = synth.process() / 32768.0;
    }
    synth.noteOff();
    for (; i < numSamples; i++) {
        samples[i] = synth.process() / 32768.0;
    }

    sf_write_float(soundFile, samples, numSamples);
    sf_close(soundFile);

    delete samples;

    return 0;
}
