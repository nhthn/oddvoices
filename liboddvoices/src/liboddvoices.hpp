#pragma once
#include <deque>
#include <memory>
#include <vector>
#include <iostream>
#include <fstream>

namespace oddvoices {

class Database {
public:
    Database(std::string filename);

    auto getSampleRate() { return m_sampleRate; }
    auto getGrainLength() { return m_grainLength; }
    auto& getWavetableMemory() { return m_wavetableMemory; }

    int getNumPhonemes() { return m_phonemes.size(); }
    int phonemeToPhonemeIndex(std::string phoneme);
    std::string phonemeIndexToPhoneme(int index);

    int getNumSegments() { return m_segments.size(); }
    int segmentToSegmentIndex(std::string segment);
    std::string segmentIndexToSegment(int index);
    int segmentNumFrames(int index);
    bool segmentIsLong(int index);
    int segmentOffset(int index);

private:
    int m_sampleRate;
    int m_grainLength;
    std::vector<std::string> m_phonemes;
    std::vector<std::string> m_segments;
    std::vector<int> m_segmentsNumFrames;
    std::vector<bool> m_segmentsIsLong;
    std::vector<int> m_segmentsOffset;
    std::vector<int16_t> m_wavetableMemory;
};


class Grain {
public:
    Grain(std::shared_ptr<Database> database);

    bool isActive() { return m_active; };
    void play(int offset1, int offset2, float crossfade);

    int16_t process();

private:
    std::shared_ptr<Database> m_database;
    bool m_active = false;
    int m_offset1;
    int m_offset2;
    int m_readPos = 0;
    float m_crossfade;
};


class Synth {
public:
    Synth(float sampleRate, std::shared_ptr<Database> database);

    int32_t process();
    void setFrequency(float frequency) { m_frequency = frequency; };
    void queueSegment(int segment);
    bool isActive();

    void noteOn();
    void noteOff();

private:
    const float m_sampleRate;
    float m_phase = 1;
    float m_frequency = 200;
    std::shared_ptr<Database> m_database;
    static constexpr int m_maxGrains = 10;
    int m_nextGrain = 0;
    std::unique_ptr<Grain> m_grains[m_maxGrains];

    float m_originalF0;

    int m_noteOns = 0;
    int m_noteOffs = 0;

    int m_segment;
    float m_segmentTime;
    float m_segmentLength;
    int m_oldSegment;
    float m_oldSegmentTime;
    float m_oldSegmentLength;

    float m_crossfade;
    float m_crossfadeRamp;
    float m_crossfadeLength = 0.03;

    std::deque<int> m_segmentQueue;

    void newSegment();
    int getOffset(int segment, float segmentTime);
};


} // namespace oddvoices
