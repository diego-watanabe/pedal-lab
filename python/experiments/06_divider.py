"""06 - Flip-flop octave divider (the heart of the OC-2)

Walk through the samples keeping a state of +1 or -1. Toggle the state on
every upward zero crossing, which gives a square wave at half the input
frequency. Multiply that by the input.

Prediction: the lowest component is 55 Hz, an octave below 110 Hz, and the
output follows the input's level. Then try --signal "decay:sine:110" and a
real bass DI with --input.

To play it live with live.py, wrap it in a Processor class that keeps the
flip-flop state between blocks (see examples/dc_blocker.py).
"""
import numpy as np

SIGNAL = "sine:110"
FMAX = 1000
WINDOW_MS = 60


def process(x: np.ndarray, sr: int) -> np.ndarray:
    raise NotImplementedError("toggle on upward zero crossings, multiply by x")
