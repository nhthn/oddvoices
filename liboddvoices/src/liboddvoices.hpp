#pragma once
#include <memory>
#include <vector>
#include <iostream>
#include <fstream>

namespace oddvoices {

class Database {
public:
    Database();

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
    void play(int offset);

    int16_t process();

private:
    std::shared_ptr<Database> m_database;
    bool m_active = false;
    int m_offset;
    int m_readPos = 0;
};


class Synth {
public:
    Synth(float sampleRate, std::shared_ptr<Database> database);

    int32_t process();

private:
    float m_sampleRate;
    float m_phase = 1;
    float m_frequency = 200;
    std::shared_ptr<Database> m_database;
    const int m_maxGrains = 10;
    int m_nextGrain = 0;
    std::vector<std::unique_ptr<Grain>> m_grains;
};


} // namespace oddvoices
