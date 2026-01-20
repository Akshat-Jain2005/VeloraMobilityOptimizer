cmake_minimum_required(VERSION 3.20)

# Frontend build configuration (placeholder for future frontend logic)
message(STATUS "[Frontend] Configuring frontend components...")

file(GLOB FRONTEND_SOURCES 
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cc"
)

if(FRONTEND_SOURCES)
    add_library(velora_frontend STATIC ${FRONTEND_SOURCES})
    target_include_directories(velora_frontend 
        PUBLIC 
            ${CMAKE_CURRENT_SOURCE_DIR}/include
    )
    message(STATUS "[Frontend] Created library: velora_frontend")
else()
    message(STATUS "[Frontend] No source files found, skipping library creation")
endif()
