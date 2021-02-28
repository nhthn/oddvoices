#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include "liboddvoices.hpp"

TEST_CASE("Database metadata") {
    oddvoices::Database database("nwh.voice");
    REQUIRE(database.getSampleRate() == 44100);
    REQUIRE(database.getGrainLength() == 566);

    REQUIRE(
        database.phonemeIndexToPhoneme(
            database.phonemeToPhonemeIndex("A")
        ) == "A"
    );

    REQUIRE(
        database.segmentIndexToSegment(
            database.segmentToSegmentIndex("A")
        ) == "A"
    );

    REQUIRE(
        database.segmentNumFrames(
            database.segmentToSegmentIndex("A")
        ) == 114
    );

    REQUIRE(
        database.segmentIsLong(
            database.segmentToSegmentIndex("A")
        )
    );

    REQUIRE(
        !database.segmentIsLong(
            database.segmentToSegmentIndex("dA")
        )
    );

    auto memory = database.getWavetableMemory();
    auto offset = database.segmentOffset(database.segmentToSegmentIndex("A"));
    REQUIRE(memory[offset] == 0);
    REQUIRE(memory[offset + database.getGrainLength() / 2] != 0);
    REQUIRE(memory[offset + database.getGrainLength() - 1] == 0);
}

TEST_CASE("Synth") {
    auto database = std::make_shared<oddvoices::Database>("nwh.voice");
    oddvoices::Synth synth(44100.0f, database);

    for (int i = 0; i < 500; i++) {
        auto sample = synth.process();
        if (i == 0) {
            REQUIRE(sample == 0);
        }
        if (i == 100) {
            REQUIRE(sample != 0);
        }
    }
}
