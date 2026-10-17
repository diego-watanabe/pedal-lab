"""Each test encodes the prediction written in the experiment's docstring.

Unimplemented experiments are skipped, so `pytest` stays green while you
work through them. Run one with:  pytest -k divider
"""
import numpy as np
import pytest

from dsplab import analysis, experiment, signals

SR = 48000


def run(name, spec, duration=1.0):
    mod = experiment.load(name)
    x = signals.parse(spec, duration, SR)
    try:
        y = np.asarray(mod.process(x.copy(), SR), dtype=np.float64)
    except NotImplementedError:
        pytest.skip(f"{name} not implemented yet")
    assert y.shape == x.shape, "process() must return one sample per input sample"
    assert np.all(np.isfinite(y)), "output contains NaN or inf"
    return mod, x, y


def lvl(y, f):
    return analysis.level_at(y, SR, f)


def test_01_gain():
    mod, x, y = run("01", "sine:110")
    expected = 20 * np.log10(mod.GAIN)
    assert lvl(y, 110) == pytest.approx(expected, abs=0.05)
    assert lvl(y, 330) < -100  # linear: nothing new


def test_02_hard_clip():
    mod, x, y = run("02", "sine:110")
    assert np.max(np.abs(y)) == pytest.approx(mod.THRESHOLD, abs=1e-9)
    for f in (330, 550, 770):
        assert lvl(y, f) > -60, f"odd harmonic {f} Hz missing"
    for f in (220, 440, 660):
        assert lvl(y, f) < -90, f"even harmonic {f} Hz should be absent"


def test_03_asym_clip():
    mod, x, y = run("03", "sine:110")
    assert np.max(y) == pytest.approx(mod.POS, abs=1e-9)
    assert np.min(y) == pytest.approx(mod.NEG, abs=1e-9)
    for f in (220, 440):
        assert lvl(y, f) > -60, f"even harmonic {f} Hz missing"
    assert abs(np.mean(y)) > 0.01, "expected a DC offset"


def test_04_rectify():
    _, x, y = run("04", "sine:110")
    assert lvl(y, 220) > -20
    assert lvl(y, 110) < -90, "fundamental should be gone"
    assert np.mean(y) > 0.5, "expected a large positive DC offset"


def test_05_aliasing():
    _, x, y = run("05", "sine:5000")
    assert lvl(y, 15000) > -20  # 3rd harmonic, below Nyquist
    assert lvl(y, 23000) > -30  # 5th harmonic (25 kHz) folded back
    assert lvl(y, 13000) > -30  # 7th harmonic (35 kHz) folded back


def test_06_divider():
    _, x, y = run("06", "sine:110")
    assert lvl(y, 55) > -20, "no octave-down component at 55 Hz"
    lowest = min(f for f, l in analysis.peaks(y, SR, floor_db=-40))
    assert lowest == pytest.approx(55, abs=1)
    assert np.max(np.abs(y)) <= np.max(np.abs(x)) + 1e-9


def test_06_divider_follows_level():
    _, x, y = run("06", "decay:sine:110")
    early = np.max(np.abs(y[: SR // 10]))
    late = np.max(np.abs(y[-SR // 10 :]))
    assert late < early * 0.01, "output should decay with the input"


def test_07_one_pole_cutoff():
    mod, x, y = run("07", "sine:110")
    tail = y[SR // 2 :]  # skip the start-up transient
    level = 20 * np.log10(np.max(np.abs(tail)))
    assert level == pytest.approx(-3.0, abs=0.25)


def test_07_one_pole_impulse():
    mod, x, y = run("07", "impulse")
    assert np.all(np.diff(y[1:200]) < 0), "impulse response should decay monotonically"
    # The FFT of the impulse response is the frequency response (no window).
    h = np.abs(np.fft.rfft(y))
    f = np.fft.rfftfreq(len(y), 1 / SR)
    at_cutoff = 20 * np.log10(h[np.argmin(np.abs(f - mod.CUTOFF))] / h[0])
    assert at_cutoff == pytest.approx(-3.0, abs=0.25)


def test_08_intermodulation():
    _, x, y = run("08", "sine:110@0.5+sine:165@0.5")
    assert lvl(x, 55) < -100
    assert lvl(y, 55) > -60, "difference tone at 55 Hz missing"
