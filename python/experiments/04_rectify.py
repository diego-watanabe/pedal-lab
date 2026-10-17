"""04 - Full-wave rectifier (the Octavia trick)

Prediction: the 110 Hz fundamental disappears and the lowest component is
220 Hz, one octave up, plus a large DC offset.
"""
import numpy as np

SIGNAL = "sine:110"
FMAX = 2000


def process(x: np.ndarray, sr: int) -> np.ndarray:
    raise NotImplementedError("full-wave rectify")
