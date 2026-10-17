"""Measurements and plots for checking what a process did to a signal."""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-12))


def peak_db(x):
    return float(db(np.max(np.abs(x))))


def rms_db(x):
    return float(db(np.sqrt(np.mean(np.square(x)))))


def spectrum(x, sr):
    """Hann-windowed magnitude spectrum in dBFS.

    Scaled so a full-scale sine reads 0 dB at its frequency.
    With 1 s of audio the bins are exactly 1 Hz apart.
    """
    w = np.hanning(len(x))
    mag = np.abs(np.fft.rfft(x * w)) * 2 / np.sum(w)
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    return freqs, db(mag)


def level_at(x, sr, freq):
    """Level in dBFS of the component at `freq` Hz (max of the nearest bins)."""
    freqs, mag = spectrum(x, sr)
    i = int(np.argmin(np.abs(freqs - freq)))
    return float(np.max(mag[max(i - 1, 0) : i + 2]))


def dc_db(x):
    return float(db(np.mean(x)))


def peaks(x, sr, n=12, floor_db=-90.0, fmin=1.0):
    """Strongest spectral peaks as (freq_hz, level_db), loudest first."""
    freqs, mag = spectrum(x, sr)
    idx, _ = find_peaks(mag, height=floor_db, distance=max(1, int(5 * len(x) / sr)))
    idx = [i for i in idx if freqs[i] >= fmin]
    out = []
    for i in idx:
        f = freqs[i]
        if 0 < i < len(mag) - 1:  # parabolic interpolation for a finer frequency
            a, b, c = mag[i - 1], mag[i], mag[i + 1]
            denom = a - 2 * b + c
            if denom != 0:
                f += 0.5 * (a - c) / denom * (freqs[1] - freqs[0])
        out.append((float(f), float(mag[i])))
    out.sort(key=lambda p: -p[1])
    return out[:n]


def report(x, y, sr, n=10):
    """Print levels and the strongest peaks of input and output."""
    print(f"{'':10}{'peak':>10}{'rms':>10}{'dc':>10}")
    for name, s in (("input", x), ("output", y)):
        print(f"{name:10}{peak_db(s):>9.2f}dB{rms_db(s):>8.2f}dB{dc_db(s):>8.1f}dB")
    for name, s in (("input", x), ("output", y)):
        print(f"\n{name} peaks (Hz, dBFS):")
        for f, l in sorted(peaks(s, sr, n=n)):
            print(f"  {f:10.1f}  {l:7.2f}")


def plot(x, y, sr, path, title="", fmax=None, window_ms=None):
    """Save a 2x2 figure: waveforms (in/out) and spectra (in/out)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if window_ms is None:
        window_ms = 40.0
    n = min(len(x), int(sr * window_ms / 1000))
    t = np.arange(n) / sr * 1000

    fig, ax = plt.subplots(2, 2, figsize=(12, 7))
    fig.suptitle(title)
    for col, (name, s) in enumerate((("input", x), ("output", y))):
        ax[0, col].plot(t, s[:n], lw=1)
        ax[0, col].set_title(f"{name} waveform")
        ax[0, col].set_xlabel("ms")
        ax[0, col].set_ylim(-1.1 * max(1.0, np.max(np.abs(s))), 1.1 * max(1.0, np.max(np.abs(s))))
        ax[0, col].grid(alpha=0.3)

        f, m = spectrum(s, sr)
        ax[1, col].plot(f, m, lw=1)
        ax[1, col].set_title(f"{name} spectrum")
        ax[1, col].set_xlabel("Hz")
        ax[1, col].set_ylabel("dBFS")
        ax[1, col].set_xlim(0, fmax or sr / 2)
        ax[1, col].set_ylim(-120, 6)
        ax[1, col].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
