cmake_minimum_required(VERSION 3.20)

# Constraints module
file(GLOB CONSTRAINT_SOURCES "*.cpp" "*.cc")

if(CONSTRAINT_SOURCES)
    add_library(velora_constraints OBJECT ${CONSTRAINT_SOURCES})
    target_include_directories(velora_constraints 
        PRIVATE 
            ${CMAKE_CURRENT_SOURCE_DIR}/..
    )
    message(STATUS "[Constraints] Added constraint implementations")
endif()
