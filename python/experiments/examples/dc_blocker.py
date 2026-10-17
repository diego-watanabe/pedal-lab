"""Example: DC blocker (worked example for docs/DEVELOPMENT.md)

A one-pole, one-zero high-pass filter that removes DC offset, for example
after an asymmetric clipper:

    y[n] = g * (x[n] - x[n-1]) + R * y[n-1]

    R = exp(-2*pi*CUTOFF_HZ/sr)   pole radius: closer to 1 = lower cutoff
    g = (1 + R) / 2               makes the gain exactly 1 at Nyquist

The zero at z = 1 blocks DC completely; the pole just inside it keeps
everything above a few Hz.

Predictions:
  * the 0.3 DC offset is gone once the filter settles (it decays with a
    time constant of 1 / (2*pi*CUTOFF_HZ), about 16 ms at 10 Hz)
  * the 110 Hz tone passes almost untouched (within 0.05 dB)

Written as an explicit per-sample loop with named state (x1, y1) because the
filter has memory: this is the shape the C++ port will have.
"""
import numpy as np

SIGNAL = "sine:110@0.5+dc@0.3"
FMAX = 500
WINDOW_MS = 200

CUTOFF_HZ = 10.0


def process(x: np.ndarray, sr: int) -> np.ndarray:
    R = np.exp(-2.0 * np.pi * CUTOFF_HZ / sr)
    g = (1.0 + R) / 2.0
    y = np.empty_like(x)
    x1 = 0.0
    y1 = 0.0
    for n in range(len(x)):
        y1 = g * (x[n] - x1) + R * y1
        x1 = x[n]
        y[n] = y1
    return y
