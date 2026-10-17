"""Tests for the worked examples in experiments/examples/."""
import numpy as np
import pytest

from dsplab import analysis, experiment, signals

SR = 48000


def test_dc_blocker_removes_offset():
    mod = experiment.load("dc_blocker")
    x = signals.parse("sine:110@0.5+dc@0.3", 1.0, SR)
    y = mod.process(x.copy(), SR)
    settled = y[SR // 2 :]  # after ~30 time constants
    assert abs(np.mean(settled)) < 1e-4


def test_dc_blocker_passes_tone():
    mod = experiment.load("dc_blocker")
    x = signals.parse("sine:110@0.5", 1.0, SR)
    y = mod.process(x.copy(), SR)
    assert analysis.level_at(y, SR, 110) == pytest.approx(analysis.level_at(x, SR, 110), abs=0.05)
