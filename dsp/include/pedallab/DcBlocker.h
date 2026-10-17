#pragma once

#include "Realtime.h"

#include <cmath>
#include <numbers>
#include <span>

namespace pedallab
{

/// Removes DC offset with a one-pole, one-zero high-pass filter.
///
/// Math (ports python/experiments/examples/dc_blocker.py):
///     y[n] = g * (x[n] - x[n-1]) + R * y[n-1]
///     R = exp(-2 pi fc / fs)    pole radius
///     g = (1 + R) / 2           unity gain at Nyquist
/// The zero at z = 1 removes DC entirely; the pole sets the cutoff.
/// Aliasing: none. The filter is linear.
///
/// Coefficients and state are double. R is very close to 1 (0.9987 at 10 Hz
/// and 48 kHz), and that is where float rounding in a feedback path starts to
/// matter: at this cutoff float stays within about 1e-6 of the double result,
/// but the error grows as the cutoff drops. Double costs nothing noticeable here.
class DcBlocker
{
public:
    void prepare(double sampleRate) noexcept
    {
        currentSampleRate = sampleRate;
        updateCoefficients();
        reset();
    }

    void reset() noexcept
    {
        previousInput = 0.0;
        previousOutput = 0.0;
    }

    /// Takes effect immediately. Call from prepare-time code or between blocks.
    void setCutoffHz(double newCutoffHz) noexcept
    {
        cutoffHz = newCutoffHz;
        updateCoefficients();
    }

    [[nodiscard]] double getCutoffHz() const noexcept { return cutoffHz; }

    PEDALLAB_NONBLOCKING void process(std::span<float> block) noexcept
    {
        for (auto& sample : block)
        {
            const auto input = static_cast<double>(sample);
            previousOutput = gain * (input - previousInput) + poleRadius * previousOutput;
            previousInput = input;
            sample = static_cast<float>(previousOutput);
        }
    }

private:
    void updateCoefficients() noexcept
    {
        poleRadius = std::exp(-2.0 * std::numbers::pi * cutoffHz / currentSampleRate);
        gain = (1.0 + poleRadius) / 2.0;
    }

    double cutoffHz = 10.0;
    double currentSampleRate = 48000.0;
    double poleRadius = 0.0;
    double gain = 0.0;
    double previousInput = 0.0;
    double previousOutput = 0.0;
};

} // namespace pedallab
