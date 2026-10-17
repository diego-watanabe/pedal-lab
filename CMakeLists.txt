cmake_minimum_required(VERSION 3.25)

project(pedal-lab VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)  # for clang-tidy and editors

# Universal binary on macOS (Apple Silicon + Intel) for release builds.
if(APPLE AND NOT CMAKE_OSX_ARCHITECTURES)
    set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "" FORCE)
endif()

option(PEDALLAB_BUILD_PLUGINS "Build the JUCE plugins" ON)
option(PEDALLAB_BUILD_TESTS "Build the C++ tests" ON)
option(PEDALLAB_WERROR "Treat warnings as errors" ON)
set(PEDALLAB_SANITIZER "" CACHE STRING "Sanitizer for dev builds: address, undefined, thread or realtime")

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(Warnings)
include(Sanitizers)
include(Dependencies)

add_subdirectory(dsp)

if(PEDALLAB_BUILD_PLUGINS)
    add_subdirectory(plugins)
endif()

if(PEDALLAB_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests/cpp)
endif()
