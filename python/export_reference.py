#!/usr/bin/env python3
"""Export an experiment's input and output as reference WAVs for the C++ tests.

    python export_reference.py 01_gain
    python export_reference.py 06_divider --signal "decay:sine:110" --duration 0.5

Writes tests/cpp/reference/<experiment>/{input,output}.wav (32-bit float).
Keep references short (default 0.25 s) so the repo stays small.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from dsplab import experiment, signals, wavio

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "tests" / "cpp" / "reference"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("experiment")
    ap.add_argument("--signal")
    ap.add_argument("--duration", type=float, default=0.25)
    ap.add_argument("--sr", type=int, default=signals.DEFAULT_SR)
    args = ap.parse_args(argv)

    mod = experiment.load(args.experiment)
    name = Path(mod.__file__).stem
    spec = args.signal or getattr(mod, "SIGNAL", "sine:110")
    x = signals.parse(spec, args.duration, args.sr).astype(np.float32)
    # Process the float32-rounded input, the same samples the C++ test will read.
    y = np.asarray(mod.process(x.astype(np.float64), args.sr), dtype=np.float32)

    out = REFERENCE_DIR / name
    out.mkdir(parents=True, exist_ok=True)
    wavio.write(out / "input.wav", x, args.sr)
    wavio.write(out / "output.wav", y, args.sr)
    (out / "meta.json").write_text(
        json.dumps({"experiment": name, "signal": spec, "duration": args.duration, "sr": args.sr}, indent=2) + "\n"
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
