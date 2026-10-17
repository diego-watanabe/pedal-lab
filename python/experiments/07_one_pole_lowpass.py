"""07 - One-pole low-pass filter

    y[n] = y[n-1] + a * (x[n] - y[n-1]),   a = 1 - exp(-2*pi*CUTOFF/sr)

Predictions:
  * a sine at CUTOFF comes out about 3 dB quieter
  * an impulse (--signal impulse) comes out as a decaying exponential, and
    its spectrum is the filter's frequency response

To play it live with live.py, wrap it in a Processor class that keeps y[n-1]
between blocks (see examples/dc_blocker.py).
"""
import numpy as np

SIGNAL = "sine:110"
FMAX = 2000
WINDOW_MS = 40

CUTOFF = 110.0


def process(x: np.ndarray, sr: int) -> np.ndarray:
    raise NotImplementedError("implement the one-pole recurrence")
