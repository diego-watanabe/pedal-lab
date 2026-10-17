#include "Reference.h"
#include "TestSignals.h"

#include <pedallab/DcBlocker.h>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <numeric>
#include <span>
#include <vector>

using Catch::Approx;
using pedallab::test::sine;

namespace
{
constexpr double sampleRate = 48000.0;

float mean(std::span<const float> samples)
{
    return std::accumulate(samples.begin(), samples.end(), 0.0f) / static_cast<float>(samples.size());
}

float peak(std::span<const float> samples)
{
    float result = 0.0f;
    for (const float s : samples)
        result = std::max(result, std::abs(s));
    return result;
}
} // namespace

TEST_CASE("DcBlocker removes a constant offset", "[dcblocker]")
{
    pedallab::DcBlocker blocker;
    blocker.prepare(sampleRate);
    std::vector<float> block(48000, 0.3f);
    blocker.process(block);
    // After half a second (about 30 time constants at 10 Hz) the offset is gone.
    CHECK(std::abs(mean(std::span<const float>(block).subspan(24000))) < 1e-5f);
}

TEST_CASE("DcBlocker passes audio-range tones", "[dcblocker]")
{
    pedallab::DcBlocker blocker;
    blocker.prepare(sampleRate);
    auto block = sine(110.0, sampleRate, 48000, 0.5f);
    blocker.process(block);
    CHECK(peak(std::span<const float>(block).subspan(24000)) == Approx(0.5f).epsilon(0.005));
}

TEST_CASE("DcBlocker reset clears its state", "[dcblocker]")
{
    pedallab::DcBlocker blocker;
    blocker.prepare(sampleRate);
    std::vector<float> offset(1000, 1.0f);
    blocker.process(offset);

    blocker.reset();
    std::vector<float> silence(100, 0.0f);
    blocker.process(silence);
    CHECK(peak(silence) == 0.0f);
}

TEST_CASE("DcBlocker output does not depend on block size", "[dcblocker]")
{
    auto input = sine(110.0, sampleRate, 4800, 0.5f);
    for (auto& s : input)
        s += 0.3f;

    auto render = [&](size_t blockSize)
    {
        pedallab::DcBlocker blocker;
        blocker.prepare(sampleRate);
        auto output = input;
        for (size_t start = 0; start < output.size(); start += blockSize)
            blocker.process(std::span<float>(output).subspan(start, std::min(blockSize, output.size() - start)));
        return output;
    };

    const auto reference = render(input.size());
    for (const size_t blockSize : {1u, 7u, 64u, 512u})
    {
        INFO("block size " << blockSize);
        CHECK(render(blockSize) == reference);
    }
}

// Reference: python/experiments/examples/dc_blocker.py
// Regenerate with:  cd python && python export_reference.py dc_blocker
// Tolerance: both versions compute in double; the only difference is the
// float32 rounding of the stored output, so 1e-6 is tight but safe.
TEST_CASE("DcBlocker matches the Python prototype", "[dcblocker][reference]")
{
    const auto ref = pedallab::test::loadReference("dc_blocker");

    pedallab::DcBlocker blocker;
    blocker.prepare(ref.sampleRate);
    blocker.setCutoffHz(10.0); // must match CUTOFF_HZ in dc_blocker.py

    auto block = ref.input;
    blocker.process(block);
    pedallab::test::checkMatches(block, ref.output, 1e-6f);
}
