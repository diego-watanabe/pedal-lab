#pragma once

// Test-signal generators for C++ unit tests (may allocate; test code only).

#include <cmath>
#include <cstddef>
#include <numbers>
#include <vector>

namespace pedallab::test
{

inline std::vector<float> sine(double frequencyHz, double sampleRate, size_t numSamples, float amplitude = 1.0f)
{
    std::vector<float> samples(numSamples);
    const double phaseIncrement = 2.0 * std::numbers::pi * frequencyHz / sampleRate;
    for (size_t i = 0; i < numSamples; ++i)
        samples[i] = amplitude * static_cast<float>(std::sin(phaseIncrement * static_cast<double>(i)));
    return samples;
}

} // namespace pedallab::test
