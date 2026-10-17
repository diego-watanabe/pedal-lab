"""The live engine, tested with fake audio buffers instead of an interface."""
import numpy as np
import pytest

from dsplab import experiment, signals
from dsplab.live import LiveEngine

SR = 48000
BLOCK = 128


def run_blocks(engine, dry, channels=2):
    """Feed `dry` through engine.callback in BLOCK-sized pieces, like a stream would."""
    out = []
    for start in range(0, len(dry), BLOCK):
        block = dry[start : start + BLOCK].astype(np.float32)
        indata = np.zeros((len(block), channels), dtype=np.float32)
        indata[:, 0] = block
        outdata = np.zeros((len(block), channels), dtype=np.float32)
        engine.callback(indata, outdata, len(block), None, None)
        out.append(outdata.copy())
    return np.concatenate(out)


def test_stateful_live_output_matches_offline():
    mod = experiment.load("dc_blocker")
    dry = signals.parse("sine:110@0.5+dc@0.3", 0.5, SR).astype(np.float32)
    engine = LiveEngine(experiment.make_processor(mod, SR), SR, out_channels=(0, 1))
    live = run_blocks(engine, dry)
    offline = mod.process(dry.astype(np.float64), SR)
    np.testing.assert_allclose(live[:, 0], offline, atol=1e-6)
    np.testing.assert_array_equal(live[:, 0], live[:, 1])


def test_stateless_experiment_runs_per_block():
    mod = experiment.load("01")
    dry = signals.parse("sine:110", 0.1, SR).astype(np.float32)
    engine = LiveEngine(experiment.make_processor(mod, SR), SR, out_channels=(0,))
    live = run_blocks(engine, dry)
    np.testing.assert_allclose(live[:, 0], mod.GAIN * dry, atol=1e-7)


def test_stateful_experiment_without_processor_is_refused():
    mod = experiment.load("06")
    with pytest.raises(ValueError, match="has state"):
        experiment.make_processor(mod, SR)


def test_bypass_passes_input_through():
    mod = experiment.load("dc_blocker")
    dry = signals.parse("sine:110@0.5+dc@0.3", 0.1, SR).astype(np.float32)
    engine = LiveEngine(experiment.make_processor(mod, SR), SR, out_channels=(0,))
    engine.bypass = True
    np.testing.assert_array_equal(run_blocks(engine, dry)[:, 0], dry)


def test_recording_keeps_dry_and_wet():
    mod = experiment.load("01")
    dry = signals.parse("sine:110", 0.1, SR).astype(np.float32)
    engine = LiveEngine(experiment.make_processor(mod, SR), SR, out_channels=(0,), record_seconds=1.0)
    run_blocks(engine, dry)
    assert engine.recorded == len(dry)
    np.testing.assert_array_equal(engine.dry[: len(dry)], dry)
    np.testing.assert_allclose(engine.wet[: len(dry)], mod.GAIN * dry, atol=1e-7)


def test_errors_silence_the_output_instead_of_crashing():
    class Broken:
        def process(self, block):
            raise RuntimeError("bug in my experiment")

    engine = LiveEngine(Broken(), SR, out_channels=(0,))
    out = run_blocks(engine, np.ones(BLOCK * 2, dtype=np.float32))
    assert isinstance(engine.error, RuntimeError)
    assert np.all(out == 0.0)


def test_file_source_loops():
    mod = experiment.load("01")
    source = np.arange(10, dtype=np.float32)
    engine = LiveEngine(experiment.make_processor(mod, SR), SR, out_channels=(0,), source=source)
    outdata = np.zeros((25, 1), dtype=np.float32)
    engine.output_callback(outdata, 25, None, None)
    expected = mod.GAIN * np.concatenate([source, source, source[:5]])
    np.testing.assert_allclose(outdata[:, 0], expected)
