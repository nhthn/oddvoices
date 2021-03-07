#include "liboddvoices.hpp"

namespace oddvoices {

int32_t read32BitIntegerLE(std::ifstream& ifstream) {
    unsigned char c[4];
    ifstream.read(reinterpret_cast<char*>(c), 4);
    return c[0] | (c[1] << 8) | (c[2] << 16) | (c[3] << 24);
}

int16_t read16BitIntegerLE(std::ifstream& ifstream) {
    unsigned char c[2];
    ifstream.read(reinterpret_cast<char*>(c), 2);
    int16_t result = c[0] | (c[1] << 8);
    return result;
}

std::string readString(std::ifstream& ifstream) {
    char string[256];
    for (int i = 0; i < 256; i++) {
        char c;
        ifstream.read(&c, 1);
        string[i] = c;
        if (c == 0) {
            return string;
        }
    }
    std::cerr << "String too long" << std::endl;
    return "";
}

Database::Database(std::string filename) {
    std::ifstream stream(filename, std::ios::binary);
    if (!stream.is_open()) {
        return;
    }

    {
        char c[12];
        stream.read(c, 12);
        std::string magicWord = c;
        if (magicWord != "ODDVOICES") {
            std::cerr << "Invalid magic word" << std::endl;
            return;
        }
    }

    m_sampleRate = read32BitIntegerLE(stream);
    m_grainLength = read32BitIntegerLE(stream);

    while (true) {
        std::string phoneme = std::move(readString(stream));
        if (phoneme.size() == 0) {
            break;
        }
        m_phonemes.push_back(phoneme);
    }

    int offset = 0;
    while (true) {
        std::string segmentName = std::move(readString(stream));
        if (segmentName.size() == 0) {
            break;
        }
        int segmentNumFrames = read32BitIntegerLE(stream);
        bool segmentIsLong = read32BitIntegerLE(stream) != 0;
        m_segments.push_back(segmentName);
        m_segmentsNumFrames.push_back(segmentNumFrames);
        m_segmentsIsLong.push_back(segmentIsLong);
        m_segmentsOffset.push_back(offset);
        offset += segmentNumFrames * m_grainLength;
    }

    m_wavetableMemory.reserve(offset);
    for (int i = 0; i < offset; i++) {
        m_wavetableMemory.push_back(read16BitIntegerLE(stream));
    }
}

std::string Database::phonemeIndexToPhoneme(int index) {
    return m_phonemes[index];
}

int Database::phonemeToPhonemeIndex(std::string phoneme) {
    for (int i = 0; i < static_cast<int>(m_phonemes.size()); i++) {
        if (m_phonemes[i] == phoneme) {
            return i;
        }
    }
    return -1;
}

std::string Database::segmentIndexToSegment(int index) {
    return m_segments[index];
}

int Database::segmentToSegmentIndex(std::string segment) {
    for (int i = 0; i < static_cast<int>(m_segments.size()); i++) {
        if (m_segments[i] == segment) {
            return i;
        }
    }
    return -1;
}

int Database::segmentNumFrames(int segmentIndex) {
    if (segmentIndex < 0) {
        return 0;
    }
    return m_segmentsNumFrames[segmentIndex];
}

bool Database::segmentIsLong(int segmentIndex) {
    if (segmentIndex < 0) {
        return false;
    }
    return m_segmentsIsLong[segmentIndex];
}

int Database::segmentOffset(int segmentIndex) {
    if (segmentIndex < 0) {
        return 0;
    }
    return m_segmentsOffset[segmentIndex];
}

Grain::Grain(std::shared_ptr<Database> database)
    : m_database(database)
{
}

void Grain::play(int offset1, int offset2, float crossfade)
{
    m_readPos = 0;
    m_offset1 = offset1;
    m_offset2 = offset2;
    m_crossfade = crossfade;
    m_active = true;
}

int16_t Grain::process()
{
    if (!m_active) {
        return 0;
    }
    auto& memory = m_database->getWavetableMemory();
    auto result = m_crossfade == 0 ? memory[m_offset1 + m_readPos] : (
        memory[m_offset1 + m_readPos] * (1 - m_crossfade)
        + memory[m_offset2 + m_readPos] * m_crossfade
    );
    m_readPos += 1;
    if (m_readPos == m_database->getGrainLength()) {
        m_active = false;
    }
    return result;
}


Synth::Synth(float sampleRate, std::shared_ptr<Database> database)
    : m_sampleRate(sampleRate)
    , m_database(database)
{
    for (int i = 0; i < m_maxGrains; i++) {
        m_grains.push_back(
            std::make_unique<Grain>(m_database)
        );
    }

    m_originalF0 = m_database->getSampleRate() / (0.5 * m_database->getGrainLength());

    newSegment();
}

void Synth::queueSegment(int segment)
{
    m_segmentQueue.push_back(segment);
}

void Synth::newSegment()
{
    if (m_segmentQueue.empty()) {
        m_segment = -1;
        m_segmentTime = 0;
        m_segmentLength = 0;
        return;
    }
    m_oldSegment = m_segment;
    m_oldSegmentTime = m_segmentTime;

    m_segment = m_segmentQueue[0];
    m_segmentQueue.pop_front();
    m_segmentTime = 0;
    if (m_segment == -1) {
        m_segmentLength = 0;
    } else {
        m_segmentLength = m_database->segmentNumFrames(m_segment) / m_originalF0;
    }
    if (m_oldSegment == -1) {
        m_crossfade = 0;
        m_crossfadeRamp = 0;
    } else {
        m_crossfade = 1;
        m_crossfadeRamp = -1 / (m_crossfadeLength * m_sampleRate);
    }
}

bool Synth::isActive()
{
    return m_segment != -1;
}

void Synth::noteOn()
{
    m_noteOns += 1;
}

void Synth::noteOff()
{
    m_noteOffs += 1;
}

int Synth::getOffset(int segment, float segmentTime)
{
    if (segment == -1) {
        return 0;
    }
    int segmentNumFrames = m_database->segmentNumFrames(segment);
    int frameIndex = segmentTime * m_originalF0;
    frameIndex = frameIndex % segmentNumFrames;
    int segmentOffset = m_database->segmentOffset(segment);
    int offset = segmentOffset + frameIndex * m_database->getGrainLength();
    return offset;
}

int32_t Synth::process()
{
    // 1. If the synth is inactive and there are no pending note ons, return silence.
    if (!isActive() && m_noteOns == 0) {
        return 0;
    }

    // 2. If the synth is inactive and there are pending note ons...
    // 2a. if the segment queue is empty, return silence.
    // 2b. if the segment queue is not empty, start a new segment.
    if (!isActive() && m_noteOns != 0) {
        if (m_segmentQueue.empty()) {
            return 0;
        } else {
            m_noteOns -= 1;
            newSegment();
        }
    }

    // 3. If the synth is active and there are pending note offs, AND we are currently
    // playing a long segment, then proceed to the next segment.
    if (isActive() && m_noteOffs != 0) {
        if (m_database->segmentIsLong(m_segment)) {
            m_noteOffs -= 1;
            newSegment();
        }
    }

    if (m_segmentTime >= m_segmentLength - m_crossfadeLength) {
        if (m_database->segmentIsLong(m_segment)) {
            m_segmentTime = 0;
        } else {
            newSegment();
        }
    }

    if (m_phase >= 1) {
        m_phase -= 1;

        auto offset = getOffset(m_segment, m_segmentTime);
        auto oldOffset = getOffset(m_oldSegment, m_oldSegmentTime);

        m_grains[m_nextGrain]->play(offset, oldOffset, m_crossfade);
        m_nextGrain = (m_nextGrain + 1) % m_maxGrains;
    }
    m_segmentTime += 1.0 / m_sampleRate;
    m_oldSegmentTime += 1.0 / m_sampleRate;
    m_crossfade = std::max(m_crossfade + m_crossfadeRamp, 0.0f);
    m_phase += m_frequency / m_sampleRate;

    int32_t result = 0;
    for (int i = 0; i < static_cast<int>(m_grains.size()); i++) {
        result += m_grains[i]->process();
    }
    return result;
}


} // namespace oddvoices
