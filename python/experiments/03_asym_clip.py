"""03 - Asymmetric clip

Clamp the top at POS and the bottom at NEG.

Prediction: even harmonics (220, 440 Hz ...) now appear alongside the odd
ones, plus a DC offset.
"""
import numpy as np

SIGNAL = "sine:110"
FMAX = 2000

POS = 0.5
NEG = -0.8


def process(x: np.ndarray, sr: int) -> np.ndarray:
    raise NotImplementedError("clamp the top at POS and the bottom at NEG")
