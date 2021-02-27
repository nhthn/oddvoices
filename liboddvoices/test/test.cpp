#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include "liboddvoices.hpp"

TEST_CASE("Database works") {
    oddvoices::Database database;
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
}
