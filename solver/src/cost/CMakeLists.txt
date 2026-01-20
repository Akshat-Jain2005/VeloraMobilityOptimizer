cmake_minimum_required(VERSION 3.20)

# Cost function module
file(GLOB COST_SOURCES "*.cpp" "*.cc")

if(COST_SOURCES)
    add_library(velora_cost OBJECT ${COST_SOURCES})
    target_include_directories(velora_cost 
        PRIVATE 
            ${CMAKE_CURRENT_SOURCE_DIR}/..
    )
    message(STATUS "[Cost] Added cost function implementations")
endif()
