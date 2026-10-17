"""Loading experiment modules.

An experiment is a .py file in experiments/ that defines:

    def process(x: np.ndarray, sr: int) -> np.ndarray

and optionally:

    SIGNAL = "sine:110"   # default input spec (see signals.parse)
    FMAX = 2000           # upper limit for the spectrum plot, Hz
    WINDOW_MS = 40        # length of the waveform plot, ms
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent / "experiments"


def resolve(name_or_path: str) -> Path:
    p = Path(name_or_path)
    if p.suffix == ".py" and p.exists():
        return p.resolve()
    matches = sorted(EXPERIMENTS_DIR.rglob(f"{name_or_path}*.py"))
    if not matches:
        raise FileNotFoundError(f"No experiment matching {name_or_path!r} in {EXPERIMENTS_DIR}")
    return matches[0]


class _StatelessProcessor:
    """Lets a stateless process(x, sr) run block by block."""

    def __init__(self, module, sr):
        self._process = module.process
        self._sr = sr

    def reset(self):
        pass

    def process(self, block):
        return self._process(block, self._sr)


def make_processor(module, sr):
    """A block-by-block processor for live use.

    Uses the module's Processor class if it has one. Otherwise, if the module
    declares STATELESS = True, calls process() on each block. Anything else is
    refused: calling a stateful process() per block would reset its state every
    block, the classic porting bug.
    """
    if hasattr(module, "Processor"):
        return module.Processor(sr)
    if getattr(module, "STATELESS", False):
        return _StatelessProcessor(module, sr)
    raise ValueError(
        f"{module.__name__} has state, so it can't run live yet. Add a Processor class "
        "(see experiments/examples/dc_blocker.py), or set STATELESS = True if process() "
        "keeps no state between samples."
    )


def load(name_or_path: str):
    path = resolve(name_or_path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "process"):
        raise AttributeError(f"{path} does not define process(x, sr)")
    return module
