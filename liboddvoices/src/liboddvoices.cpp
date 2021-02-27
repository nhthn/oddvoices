#include "liboddvoices.hpp"

namespace oddvoices {

int32_t read32BitIntegerLE(std::ifstream& ifstream) {
    unsigned char c[4];
    ifstream.read(reinterpret_cast<char*>(c), 4);
    return c[0] | (c[1] << 8) | (c[2] << 16) | (c[3] << 24);
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

} // namespace oddvoices
