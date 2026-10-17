# The DSP library: plain C++20, no JUCE, no allocation in process calls.
# Everything that makes sound lives here so it can be tested on its own and
# reused by every target (desktop plugins, iOS/AUv3, WebAssembly).
add_library(pedallab_dsp INTERFACE)
add_library(pedallab::dsp ALIAS pedallab_dsp)
target_include_directories(pedallab_dsp INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_features(pedallab_dsp INTERFACE cxx_std_20)
target_link_libraries(pedallab_dsp INTERFACE pedallab_sanitizers)
