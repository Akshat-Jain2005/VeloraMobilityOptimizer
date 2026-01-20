cmake_minimum_required(VERSION 3.20)

# Heuristics module
file(GLOB HEURISTIC_SOURCES "*.cpp" "*.cc")

if(HEURISTIC_SOURCES)
    add_library(velora_heuristics OBJECT ${HEURISTIC_SOURCES})
    target_include_directories(velora_heuristics 
        PRIVATE 
            ${CMAKE_CURRENT_SOURCE_DIR}/..
    )
    message(STATUS "[Heuristics] Added heuristic implementations")
endif()
