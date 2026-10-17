"""Test-signal generators.

Every generator returns a 1-D float64 numpy array. Amplitudes are linear,
1.0 = digital full scale.
"""
from __future__ import annotations

import numpy as np

DEFAULT_SR = 48000


def timebase(duration: float, sr: int = DEFAULT_SR) -> np.ndarray:
    return np.arange(int(round(duration * sr))) / sr


def sine(freq, duration=1.0, sr=DEFAULT_SR, amp=1.0, phase=0.0):
    t = timebase(duration, sr)
    return amp * np.sin(2 * np.pi * freq * t + phase)


def saw(freq, duration=1.0, sr=DEFAULT_SR, amp=1.0):
    """Naive (aliasing) sawtooth, -amp..amp."""
    t = timebase(duration, sr)
    return amp * (2.0 * ((freq * t) % 1.0) - 1.0)


def square(freq, duration=1.0, sr=DEFAULT_SR, amp=1.0):
    """Naive (aliasing) square wave."""
    return amp * np.sign(sine(freq, duration, sr))


def triangle(freq, duration=1.0, sr=DEFAULT_SR, amp=1.0):
    return amp * (2.0 * np.abs(saw(freq, duration, sr)) - 1.0)


def sweep(f0, f1, duration=1.0, sr=DEFAULT_SR, amp=1.0):
    """Exponential (log) sine sweep from f0 to f1 Hz."""
    t = timebase(duration, sr)
    k = np.log(f1 / f0)
    phase = 2 * np.pi * f0 * duration / k * (np.exp(t * k / duration) - 1.0)
    return amp * np.sin(phase)


def impulse(duration=1.0, sr=DEFAULT_SR, amp=1.0, at=0):
    """Unit impulse (Kronecker delta) at sample index `at`."""
    x = np.zeros(int(round(duration * sr)))
    x[at] = amp
    return x


def noise(duration=1.0, sr=DEFAULT_SR, amp=1.0, seed=0):
    rng = np.random.default_rng(seed)
    return amp * rng.uniform(-1.0, 1.0, int(round(duration * sr)))


def decay(x, sr=DEFAULT_SR, seconds=1.0):
    """Apply an exponential fade (60 dB down after `seconds`), like a plucked note."""
    t = np.arange(len(x)) / sr
    return x * 10 ** (-3 * t / seconds)


def mix(*signals):
    """Sum signals, padding shorter ones with zeros."""
    n = max(len(s) for s in signals)
    out = np.zeros(n)
    for s in signals:
        out[: len(s)] += s
    return out


def parse(spec: str, duration=1.0, sr=DEFAULT_SR) -> np.ndarray:
    """Build a signal from a short text spec.

    Terms are joined with '+'; each term may end with '@amp'.
        sine:110             110 Hz sine, full scale
        sine:110@0.5         same, at half amplitude
        sine:110+sine:165    two tones summed
        saw:55, square:110, triangle:220
        sweep:20-20000       exponential sweep
        impulse              unit impulse at sample 0
        noise                white noise
        dc                   constant offset (use with @, e.g. dc@0.3)
        decay:sine:110       sine with a 1 s exponential decay
    """
    terms = []
    for term in spec.split("+"):
        term = term.strip()
        amp = 1.0
        if "@" in term:
            term, a = term.rsplit("@", 1)
            amp = float(a)
        terms.append(_term(term, duration, sr) * amp)
    return mix(*terms)


def _term(term, duration, sr):
    kind, _, arg = term.partition(":")
    if kind == "decay":
        return decay(_term(arg, duration, sr), sr)
    if kind in ("sine", "saw", "square", "triangle"):
        return {"sine": sine, "saw": saw, "square": square, "triangle": triangle}[kind](
            float(arg), duration, sr
        )
    if kind == "sweep":
        f0, f1 = (float(v) for v in arg.split("-"))
        return sweep(f0, f1, duration, sr)
    if kind == "impulse":
        return impulse(duration, sr)
    if kind == "noise":
        return noise(duration, sr)
    if kind == "dc":
        return np.ones(int(round(duration * sr)))
    raise ValueError(f"Unknown signal term: {term!r}")
