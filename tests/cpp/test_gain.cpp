#include "Reference.h"

#include <pedallab/Gain.h>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <span>
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

// A processor must give the same output whether the host sends one big block
// or many small ones (docs/CPP_STANDARDS.md section 5).
TEST_CASE("Gain output does not depend on block size", "[gain]")
{
    constexpr size_t numSamples = 4800;
    std::vector<float> input(numSamples);
    for (size_t i = 0; i < numSamples; ++i)
        input[i] = std::sin(static_cast<float>(i) * 0.05f);

    auto render = [&](size_t blockSize)
    {
        pedallab::Gain gain;
        gain.prepare(48000.0);
        gain.setGainDecibels(-12.0f); // starts a ramp that crosses block boundaries
        auto output = input;
        for (size_t start = 0; start < numSamples; start += blockSize)
        {
            const auto length = std::min(blockSize, numSamples - start);
            gain.process(std::span<float>(output).subspan(start, length));
        }
        return output;
    };

    const auto reference = render(numSamples);
    for (const size_t blockSize : {1u, 7u, 64u, 512u})
    {
        INFO("block size " << blockSize);
        CHECK(render(blockSize) == reference);
    }
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
