#include "Reference.h"

#include <pedallab/Gain.h>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <vector>

using Catch::Approx;

TEST_CASE("Gain defaults to unity", "[gain]")
{
    pedallab::Gain gain;
    gain.prepare(48000.0);
    std::vector<float> block{0.25f, -0.5f, 1.0f};
    const auto original = block;
    gain.process(block);
    CHECK(block == original);
}

TEST_CASE("Gain in decibels", "[gain]")
{
    pedallab::Gain gain;
    gain.prepare(48000.0);
    gain.setGainDecibels(-6.0f);
    gain.reset();
    std::vector<float> block(64, 1.0f);
    gain.process(block);
    CHECK(block.back() == Approx(0.501187f).epsilon(1e-5));
}

TEST_CASE("Gain changes ramp instead of jumping", "[gain]")
{
    pedallab::Gain gain;
    gain.prepare(48000.0);
    gain.setGainLinear(0.0f);
    std::vector<float> block(2000, 1.0f);
    gain.process(block);

    float biggestStep = 0.0f;
    for (size_t i = 1; i < block.size(); ++i)
        biggestStep = std::max(biggestStep, std::abs(block[i] - block[i - 1]));
    CHECK(biggestStep < 0.002f); // 20 ms ramp at 48 kHz: about 0.001 per sample
    CHECK(block.back() == 0.0f);
}

// The Python prototype (python/experiments/01_gain.py) is the reference.
// Regenerate with:  cd python && python export_reference.py 01_gain
TEST_CASE("Gain matches the Python prototype", "[gain][reference]")
{
    const auto ref = pedallab::test::loadReference("01_gain");

    pedallab::Gain gain;
    gain.prepare(ref.sampleRate);
    gain.setGainLinear(0.5f); // must match GAIN in 01_gain.py
    gain.reset();

    auto block = ref.input;
    gain.process(block);
    pedallab::test::checkMatches(block, ref.output, 1e-6f);
}
