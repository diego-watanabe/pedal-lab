"""08 - Intermodulation

Feed two tones a fifth apart (110 + 165 Hz) through your clipper from 02.

Prediction: besides harmonics of each tone, sum and difference tones appear.
The difference tone at 55 Hz is the giveaway: neither input has it.
"""
import numpy as np

# No state is kept between samples, so live.py can call process() per block.
STATELESS = True

SIGNAL = "sine:110@0.5+sine:165@0.5"
FMAX = 1000
WINDOW_MS = 60

THRESHOLD = 0.4


def process(x: np.ndarray, sr: int) -> np.ndarray:
    raise NotImplementedError("clip the two-tone signal")
