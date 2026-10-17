"""05 - Squaring a high sine (meet aliasing)

Turn the sine into a square wave with sign().

Prediction: odd harmonics of 5 kHz at 15 kHz, then 25 kHz, 35 kHz ...
Anything above Nyquist (24 kHz) folds back: 25 kHz lands at 23 kHz, 35 kHz
at 13 kHz. Those folded peaks are aliasing. Try --signal "sine:110" too.
"""
import numpy as np

# No state is kept between samples, so live.py can call process() per block.
STATELESS = True

SIGNAL = "sine:5000"
FMAX = 24000
WINDOW_MS = 2


def process(x: np.ndarray, sr: int) -> np.ndarray:
    raise NotImplementedError("square the signal up")
