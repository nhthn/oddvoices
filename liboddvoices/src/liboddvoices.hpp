#pragma once
#include <fstream>

namespace oddvoices {

class Database {
public:
    Database();

    auto getSampleRate() { return m_sampleRate; }
    auto getGrainLength() { return m_grainLength; }

private:
    int m_sampleRate;
    int m_grainLength;
};

} // namespace oddvoices
