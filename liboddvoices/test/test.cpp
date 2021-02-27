#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include "liboddvoices.hpp"

TEST_CASE("Database works") {
    oddvoices::Database database;
    REQUIRE(database.getSampleRate() == 44100);
    REQUIRE(database.getGrainLength() == 566);
}
