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


def load(name_or_path: str):
    path = resolve(name_or_path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "process"):
        raise AttributeError(f"{path} does not define process(x, sr)")
    return module
