#include "liboddvoices.hpp"

namespace oddvoices {

int read32BitIntegerLE(std::ifstream& ifstream) {
    unsigned char c[4];
    ifstream.read(reinterpret_cast<char*>(c), 4);
    return c[0] | (c[1] << 8) | (c[2] << 16) | (c[3] << 24);
}

Database::Database() {
    std::string filename = "nwh.voice";
    std::ifstream stream(filename, std::ios::binary);
    if (!stream.is_open()) {
        return;
    }

    {
        char c[12];
        stream.read(&c[0], 12);
    }

    m_sampleRate = read32BitIntegerLE(stream);
    m_grainLength = read32BitIntegerLE(stream);
}

} // namespace oddvoices
