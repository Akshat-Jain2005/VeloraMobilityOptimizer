cmake_minimum_required(VERSION 3.20)

# Metaheuristics module
file(GLOB METAHEURISTIC_SOURCES "*.cpp" "*.cc")

if(METAHEURISTIC_SOURCES)
    add_library(velora_metaheuristics OBJECT ${METAHEURISTIC_SOURCES})
    target_include_directories(velora_metaheuristics 
        PRIVATE 
            ${CMAKE_CURRENT_SOURCE_DIR}/..
    )
    message(STATUS "[Metaheuristics] Added metaheuristic implementations")
endif()
