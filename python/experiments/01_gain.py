"""01 - Gain

Multiply every sample by a constant. This is the one finished example:
copy its shape for the others.

Prediction: the 110 Hz peak drops by 20*log10(0.5) = -6.02 dB, and no new
frequencies appear (gain is linear).
"""
import numpy as np

SIGNAL = "sine:110"
FMAX = 1000

GAIN = 0.5


def process(x: np.ndarray, sr: int) -> np.ndarray:
    return GAIN * x
