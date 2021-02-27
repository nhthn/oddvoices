#pragma once
#include <vector>
#include <iostream>
#include <fstream>

namespace oddvoices {

class Database {
public:
    Database();

    auto getSampleRate() { return m_sampleRate; }
    auto getGrainLength() { return m_grainLength; }

    int getNumPhonemes() { return m_phonemes.size(); }
    int phonemeToPhonemeIndex(std::string phoneme);
    std::string phonemeIndexToPhoneme(int index);

    int segmentToSegmentIndex(std::string segment);
    std::string segmentIndexToSegment(int index);
    int segmentNumFrames(int index);
    bool segmentIsLong(int index);

private:
    int m_sampleRate;
    int m_grainLength;
    std::vector<std::string> m_phonemes;
    std::vector<std::string> m_segments;
    std::vector<int> m_segmentsNumFrames;
    std::vector<bool> m_segmentsIsLong;
};

} // namespace oddvoices
