cmake_minimum_required(VERSION 3.19)

project(liboddvoices)

include_directories(src)

file(GLOB source_files src/*.cpp)
file(GLOB test_files test/*.cpp)
add_executable(liboddvoices_test ${source_files} ${test_files})

if(CMAKE_COMPILER_IS_GNUCC OR CMAKE_COMPILER_IS_GNUCXX)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Werror -Wpedantic")
endif()
