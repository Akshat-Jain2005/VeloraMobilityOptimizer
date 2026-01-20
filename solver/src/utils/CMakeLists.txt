cmake_minimum_required(VERSION 3.20)

# Utilities module
file(GLOB UTIL_SOURCES "*.cpp" "*.cc")

if(UTIL_SOURCES)
    add_library(velora_utils OBJECT ${UTIL_SOURCES})
    target_include_directories(velora_utils 
        PRIVATE 
            ${CMAKE_CURRENT_SOURCE_DIR}/..
    )
    message(STATUS "[Utils] Added utility implementations")
endif()
