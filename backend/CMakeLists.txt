cmake_minimum_required(VERSION 3.20)

# Backend library (placeholder for future backend logic)
message(STATUS "[Backend] Configuring backend components...")

file(GLOB BACKEND_SOURCES 
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cc"
)

if(BACKEND_SOURCES)
    add_library(velora_backend STATIC ${BACKEND_SOURCES})
    target_include_directories(velora_backend 
        PUBLIC 
            ${CMAKE_CURRENT_SOURCE_DIR}/include
    )
    message(STATUS "[Backend] Created library: velora_backend")
else()
    message(STATUS "[Backend] No source files found, skipping library creation")
endif()
