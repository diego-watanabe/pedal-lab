#pragma once

#include "Realtime.h"

#include <cmath>
#include <span>

namespace pedallab
{

/// Gain with a linear ramp between settings, so parameter changes don't click.
///
/// Math: y[n] = g[n] * x[n], where g ramps linearly to each new target over
/// 20 ms. Ports python/experiments/01_gain.py.
/// Aliasing: none. Gain is linear, so it creates no new frequencies.
///
/// The template for every processor in this library:
///   prepare()  called off the audio thread when the sample rate is known
///   reset()    clears state; snaps smoothed values to their targets
///   set...()   safe to call from the audio thread between blocks
///   process()  the audio-thread work: no allocation, no locks, no I/O
class Gain
{
public:
    void prepare(double sampleRate) noexcept
    {
        rampSamples = static_cast<int>(std::lround(sampleRate * rampSeconds));
        reset();
    }

    void reset() noexcept
    {
        current = target;
        remaining = 0;
    }

    void setGainLinear(float newGain) noexcept
    {
        if (newGain == target)
            return;
        target = newGain;
        remaining = rampSamples;
        step = remaining > 0 ? (target - current) / static_cast<float>(remaining) : 0.0f;
        if (remaining == 0)
            current = target;
    }

    void setGainDecibels(float dB) noexcept { setGainLinear(std::pow(10.0f, dB / 20.0f)); }

    [[nodiscard]] float getGainLinear() const noexcept { return target; }

    PEDALLAB_NONBLOCKING void process(std::span<float> block) noexcept
    {
        for (auto& sample : block)
        {
            if (remaining > 0)
            {
                current += step;
                if (--remaining == 0)
                    current = target;
            }
            sample *= current;
        }
    }

private:
    static constexpr double rampSeconds = 0.02;

    float target = 1.0f;
    float current = 1.0f;
    float step = 0.0f;
    int rampSamples = 0;
    int remaining = 0;
};

} // namespace pedallab
