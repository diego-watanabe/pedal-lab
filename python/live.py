#!/usr/bin/env python3
"""Play your instrument through an experiment in real time.

    python live.py --list-devices
    python live.py dc_blocker --device Babyface
    python live.py 02 --device Babyface --in-channel 3 --out-channels 1,2
    python live.py dc_blocker --file ../captures/di/stingray.wav      # no instrument needed
    python live.py 06 --device Babyface --record takes/slides           # keep what you played

While running:  Enter = toggle bypass (A/B)   r + Enter = reset state   q + Enter = quit

The experiment needs a Processor class, or STATELESS = True for experiments
whose process() keeps no state (see dsplab/live.py).

This is for judging how a prototype feels under your hands. Python can't
guarantee real-time behavior: expect an occasional click, and more latency
than the final plugin. Lower --blocksize for less latency, raise it if you
hear dropouts.
"""
from __future__ import annotations

import argparse
import gc
import sys
import threading
import time
from pathlib import Path

import numpy as np

from dsplab import experiment, wavio
from dsplab.live import LiveEngine


def import_sounddevice():
    try:
        import sounddevice as sd
    except OSError as e:  # the PortAudio library itself is missing (Linux)
        sys.exit(f"Audio library not available: {e}\nOn Linux: sudo apt install libportaudio2")
    except ImportError:
        sys.exit("sounddevice is not installed: pip install -r requirements.txt")
    return sd


def parse_channels(text):
    return tuple(int(c) - 1 for c in text.split(","))


def parse_device(text):
    if text is None:
        return None
    return int(text) if text.isdigit() else text


def keyboard(engine, stop):
    """Reads commands from the terminal on a background thread."""
    for line in sys.stdin:
        cmd = line.strip().lower()
        if cmd == "q":
            break
        if cmd == "r":
            engine.reset_requested = True
        else:
            engine.bypass = not engine.bypass
    stop.set()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("experiment", nargs="?", help="experiment number/name prefix or path")
    ap.add_argument("--list-devices", action="store_true", help="show audio devices and exit")
    ap.add_argument("--device", help="device name (or part of it) or index, e.g. Babyface")
    ap.add_argument("--in-channel", type=int, default=1, help="input channel, 1-based (default 1)")
    ap.add_argument("--out-channels", default="1,2", help="output channels, 1-based (default 1,2)")
    ap.add_argument("--sr", type=int, default=48000, help="sample rate (default 48000)")
    ap.add_argument("--blocksize", type=int, default=128, help="samples per block (default 128)")
    ap.add_argument("--exclusive", action="store_true", help="WASAPI exclusive mode (Windows, lower latency)")
    ap.add_argument("--file", type=Path, help="loop a WAV file as the input instead of the interface")
    ap.add_argument("--record", type=Path, help="folder to save dry.wav and wet.wav when you quit")
    ap.add_argument("--record-seconds", type=float, default=600, help="max recording length (default 600)")
    args = ap.parse_args(argv)

    sd = import_sounddevice()
    if args.list_devices:
        print(sd.query_devices())
        print("\nHost APIs:", ", ".join(api["name"] for api in sd.query_hostapis()))
        print("On Windows, pick an ASIO device if one is listed, otherwise WASAPI with --exclusive.")
        return 0
    if not args.experiment:
        ap.error("name an experiment, or use --list-devices")

    module = experiment.load(args.experiment)
    try:
        processor = experiment.make_processor(module, args.sr)
    except ValueError as e:
        sys.exit(str(e))

    # Run one block before the stream starts so numba compiles now, not in the first callback.
    processor.process(np.zeros(args.blocksize))
    if hasattr(processor, "reset"):
        processor.reset()

    source = None
    if args.file:
        source, file_sr = wavio.read(args.file)
        if file_sr != args.sr:
            sys.exit(f"{args.file} is {file_sr} Hz; run with --sr {file_sr}")

    engine = LiveEngine(
        processor,
        args.sr,
        in_channel=args.in_channel - 1,
        out_channels=parse_channels(args.out_channels),
        record_seconds=args.record_seconds if args.record else 0.0,
        source=source,
    )

    out_ch = max(engine.out_channels) + 1
    extra = sd.WasapiSettings(exclusive=True) if args.exclusive else None
    common = dict(samplerate=args.sr, blocksize=args.blocksize, dtype="float32", latency="low", extra_settings=extra)
    device = parse_device(args.device)
    if source is not None:
        stream = sd.OutputStream(device=device, channels=out_ch, callback=engine.output_callback, **common)
    else:
        stream = sd.Stream(device=device, channels=(args.in_channel, out_ch), callback=engine.callback, **common)

    stop = threading.Event()
    threading.Thread(target=keyboard, args=(engine, stop), daemon=True).start()

    name = Path(module.__file__).stem
    print(f"{name} live at {args.sr} Hz, {args.blocksize}-sample blocks")
    print("Enter = bypass on/off, r = reset, q = quit\n")

    gc.disable()  # garbage collection pauses are a common cause of clicks
    try:
        with stream:
            in_ms = stream.latency[0] * 1000 if isinstance(stream.latency, tuple) else 0.0
            out_ms = (stream.latency[1] if isinstance(stream.latency, tuple) else stream.latency) * 1000
            print(f"Reported latency: input {in_ms:.1f} ms + output {out_ms:.1f} ms")
            while not stop.is_set() and engine.error is None:
                state = "BYPASS" if engine.bypass else "ON    "
                print(f"\r{state}  cpu {stream.cpu_load * 100:5.1f}%  dropouts {engine.underruns}   ", end="", flush=True)
                time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        gc.enable()
        print()

    if engine.error is not None:
        print(f"Stopped: process() raised {engine.error!r}", file=sys.stderr)

    if args.record and engine.recorded:
        args.record.mkdir(parents=True, exist_ok=True)
        wavio.write(args.record / "dry.wav", engine.dry[: engine.recorded], args.sr)
        wavio.write(args.record / "wet.wav", engine.wet[: engine.recorded], args.sr)
        print(f"Saved {engine.recorded / args.sr:.1f} s to {args.record}/ (dry.wav is the input as played)")
    return 1 if engine.error is not None else 0


if __name__ == "__main__":
    sys.exit(main())
