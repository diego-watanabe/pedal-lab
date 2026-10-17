"""02 - Symmetric hard clip

Clamp the signal to +/-THRESHOLD.

Prediction: odd harmonics appear (330, 550, 770 Hz ...) and even harmonics
(220, 440 Hz ...) stay absent, because the clipping is symmetric.
"""
import numpy as np

SIGNAL = "sine:110"
FMAX = 2000

THRESHOLD = 0.5


def process(x: np.ndarray, sr: int) -> np.ndarray:
    raise NotImplementedError("clamp x to +/-THRESHOLD")
