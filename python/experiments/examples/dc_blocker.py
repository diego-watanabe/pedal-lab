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

Structure, which every stateful experiment can copy:
  * _kernel: the per-sample loop, compiled by numba. State (x[n-1], y[n-1])
    lives in a small array passed in and updated in place.
  * Processor: holds coefficients and state between blocks, so live.py can
    run it in real time. Same shape as the C++ class (prepare/reset/process).
  * process(x, sr): the whole-signal entry point run.py and the tests use.
"""
import numba
import numpy as np

SIGNAL = "sine:110@0.5+dc@0.3"
FMAX = 500
WINDOW_MS = 200

CUTOFF_HZ = 10.0


@numba.njit
def _kernel(x, y, state, R, g):
    x1 = state[0]
    y1 = state[1]
    for n in range(len(x)):
        y1 = g * (x[n] - x1) + R * y1
        x1 = x[n]
        y[n] = y1
    state[0] = x1
    state[1] = y1


class Processor:
    def __init__(self, sr):
        self.R = np.exp(-2.0 * np.pi * CUTOFF_HZ / sr)
        self.g = (1.0 + self.R) / 2.0
        self.state = np.zeros(2)  # [x[n-1], y[n-1]]

    def reset(self):
        self.state[:] = 0.0

    def process(self, block):
        out = np.empty_like(block)
        _kernel(block, out, self.state, self.R, self.g)
        return out


def process(x: np.ndarray, sr: int) -> np.ndarray:
    return Processor(sr).process(x)
