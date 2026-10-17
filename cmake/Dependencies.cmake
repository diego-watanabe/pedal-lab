# Third-party code, pinned to exact versions and fetched at configure time.
# Downloads are cached in build/_deps; delete that folder to refetch.
include(FetchContent)

if(PEDALLAB_BUILD_PLUGINS)
    FetchContent_Declare(JUCE
        GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
        GIT_TAG 9.0.3
        GIT_SHALLOW ON
        SYSTEM)  # JUCE headers are "system" headers: our strict warnings skip them
    FetchContent_MakeAvailable(JUCE)
endif()

if(PEDALLAB_BUILD_TESTS)
    FetchContent_Declare(Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG v3.16.0
        GIT_SHALLOW ON)
    FetchContent_MakeAvailable(Catch2)
endif()
