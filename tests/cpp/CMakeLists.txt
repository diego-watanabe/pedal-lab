add_executable(pedallab_tests
    test_dc_blocker.cpp
    test_gain.cpp)

target_link_libraries(pedallab_tests PRIVATE
    pedallab::dsp
    pedallab_warnings
    Catch2::Catch2WithMain)

target_compile_definitions(pedallab_tests PRIVATE
    PEDALLAB_REFERENCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/reference")

include(Catch)
catch_discover_tests(pedallab_tests)
