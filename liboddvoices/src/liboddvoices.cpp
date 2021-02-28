#include "liboddvoices.hpp"

namespace oddvoices {

int32_t read32BitIntegerLE(std::ifstream& ifstream) {
    unsigned char c[4];
    ifstream.read(reinterpret_cast<char*>(c), 4);
    return c[0] | (c[1] << 8) | (c[2] << 16) | (c[3] << 24);
}

int32_t read16BitIntegerLE(std::ifstream& ifstream) {
    char c[2];
    ifstream.read(c, 2);
    return c[0] | (c[1] << 8);
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

Database::Database() {
    std::string filename = "nwh.voice";
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
    return m_segmentsNumFrames[segmentIndex];
}

bool Database::segmentIsLong(int segmentIndex) {
    return m_segmentsIsLong[segmentIndex];
}

int Database::segmentOffset(int segmentIndex) {
    return m_segmentsOffset[segmentIndex];
}

} // namespace oddvoices
