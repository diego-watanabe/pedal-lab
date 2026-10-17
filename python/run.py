#!/usr/bin/env python3
"""Run an experiment: generate (or load) a signal, process it, save and measure.

Examples
    python run.py 01                      # experiments/01_gain.py with its default signal
    python run.py 02 --signal "sine:110@0.8"
    python run.py 06 --signal "decay:sine:41.2" --duration 2
    python run.py 06 --input ../captures/di/stingray_low_e.wav

Outputs go to renders/<experiment>/: input.wav, output.wav, plot.png.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from dsplab import analysis, experiment, signals, wavio

HERE = Path(__file__).resolve().parent


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("experiment", help="experiment number/name prefix or path, e.g. 01 or 06_divider")
    ap.add_argument("--signal", help="input spec, e.g. 'sine:110' or 'sine:110+sine:165@0.5'")
    ap.add_argument("--input", type=Path, help="process a WAV file instead of a generated signal")
    ap.add_argument("--duration", type=float, default=1.0, help="seconds (default 1)")
    ap.add_argument("--sr", type=int, default=signals.DEFAULT_SR, help="sample rate (default 48000)")
    ap.add_argument("--fmax", type=float, help="spectrum plot upper limit in Hz")
    ap.add_argument("--window-ms", type=float, help="waveform plot length in ms")
    ap.add_argument("--out", type=Path, help="output folder (default renders/<experiment>)")
    args = ap.parse_args(argv)

    mod = experiment.load(args.experiment)
    name = Path(mod.__file__).stem

    if args.input:
        x, sr = wavio.read(args.input)
        source = str(args.input)
    else:
        sr = args.sr
        spec = args.signal or getattr(mod, "SIGNAL", "sine:110")
        x = signals.parse(spec, args.duration, sr)
        source = spec

    try:
        y = np.asarray(mod.process(x.copy(), sr), dtype=np.float64)
    except NotImplementedError as e:
        print(f"{name}: not implemented yet. {e}")
        return 1
    if y.shape != x.shape:
        print(f"warning: output shape {y.shape} differs from input {x.shape}", file=sys.stderr)

    out = args.out or HERE / "renders" / name
    out.mkdir(parents=True, exist_ok=True)
    wavio.write(out / "input.wav", x, sr)
    wavio.write(out / "output.wav", y, sr)
    analysis.plot(
        x, y, sr, out / "plot.png",
        title=f"{name}  ({source})",
        fmax=args.fmax or getattr(mod, "FMAX", None),
        window_ms=args.window_ms or getattr(mod, "WINDOW_MS", None),
    )

    print(f"{name}  input: {source}  sr: {sr}\n")
    analysis.report(x, y, sr)
    print(f"\nSaved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
