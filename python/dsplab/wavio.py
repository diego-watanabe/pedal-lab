"""WAV reading and writing (32-bit float, so levels above 0 dBFS survive)."""
from __future__ import annotations

import warnings

import numpy as np
from scipy.io import wavfile


def write(path, x, sr):
    x = np.asarray(x, dtype=np.float32)
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    if peak > 1.0:
        warnings.warn(
            f"{path}: peak {peak:.2f} exceeds full scale. Saved as float WAV, "
            "but it will clip if converted to a fixed-point format.",
            stacklevel=2,
        )
    wavfile.write(str(path), sr, x)


def read(path, mono=True):
    """Read a WAV as float64 in -1..1. Returns (samples, sample_rate)."""
    sr, data = wavfile.read(str(path))
    if np.issubdtype(data.dtype, np.integer):
        data = data.astype(np.float64) / np.iinfo(data.dtype).max
    else:
        data = data.astype(np.float64)
    if mono and data.ndim == 2:
        data = data.mean(axis=1)
    return data, sr
