#pragma once

// Reference tests compare the C++ DSP against the Python prototype.
// python/export_reference.py writes tests/cpp/reference/<name>/{input,output}.wav;
// a C++ test runs `input` through its processor and checks it against `output`.

#include "WavFile.h"

#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

#ifndef PEDALLAB_REFERENCE_DIR
    #error "PEDALLAB_REFERENCE_DIR must point at tests/cpp/reference"
#endif

namespace pedallab::test
{

struct Reference
{
    std::vector<float> input;
    std::vector<float> output;
    double sampleRate = 0.0;
};

inline Reference loadReference(const std::string& name)
{
    const std::string dir = std::string(PEDALLAB_REFERENCE_DIR) + "/" + name + "/";
    auto in = readWav(dir + "input.wav");
    auto out = readWav(dir + "output.wav");
    REQUIRE(in.sampleRate == out.sampleRate);
    REQUIRE(in.samples.size() == out.samples.size());
    return {std::move(in.samples), std::move(out.samples), static_cast<double>(in.sampleRate)};
}

/// Fails with the first mismatching sample and the overall worst error.
inline void checkMatches(const std::vector<float>& actual, const std::vector<float>& expected, float tolerance)
{
    REQUIRE(actual.size() == expected.size());
    size_t worst = 0;
    float worstError = 0.0f;
    for (size_t i = 0; i < actual.size(); ++i)
    {
        const float error = std::abs(actual[i] - expected[i]);
        if (error > worstError)
        {
            worstError = error;
            worst = i;
        }
    }
    INFO("worst error " << worstError << " at sample " << worst << ": got " << actual[worst] << ", expected "
                        << expected[worst]);
    CHECK(worstError <= tolerance);
}

} // namespace pedallab::test
