"""Real-time engine: runs an experiment on live audio, block by block.

Kept separate from the command-line script (python/live.py) and from the
sounddevice library, so the engine can be tested without an audio interface.

A live experiment needs a processor object with state that survives between
blocks (see experiment.make_processor):

    class Processor:
        def __init__(self, sr): ...          # compute coefficients, allocate state
        def reset(self): ...                 # optional: clear state
        def process(self, block): ...        # float64 block in, block out

This mirrors the C++ processors (prepare / reset / process), so a prototype
that works live is already in the shape the C++ port will take.
"""
from __future__ import annotations

import numpy as np


class LiveEngine:
    """Feeds blocks from an input (interface or file) through a processor.

    `callback` has the signature sounddevice expects for a duplex stream;
    `output_callback` is for file playback through an output-only stream.
    """

    def __init__(self, processor, sr, in_channel=0, out_channels=(0, 1), record_seconds=0.0, source=None):
        self.processor = processor
        self.sr = sr
        self.in_channel = in_channel
        self.out_channels = tuple(out_channels)
        self.source = None if source is None else np.asarray(source, dtype=np.float32)
        self.source_pos = 0

        self.bypass = False
        self.reset_requested = False
        self.underruns = 0
        self.blocks = 0
        self.error = None

        n = int(record_seconds * sr)
        self.dry = np.zeros(n, dtype=np.float32)
        self.wet = np.zeros(n, dtype=np.float32)
        self.recorded = 0

    # -- stream callbacks -------------------------------------------------

    def callback(self, indata, outdata, frames, time, status):
        """Duplex stream: instrument in, processed audio out."""
        if status:
            self.underruns += 1
        self._run(indata[:, self.in_channel], outdata)

    def output_callback(self, outdata, frames, time, status):
        """Output-only stream: a WAV file (looped) stands in for the instrument."""
        if status:
            self.underruns += 1
        self._run(self._next_source_block(frames), outdata)

    # -- internals --------------------------------------------------------

    def _next_source_block(self, frames):
        idx = (self.source_pos + np.arange(frames)) % len(self.source)
        self.source_pos = int((self.source_pos + frames) % len(self.source))
        return self.source[idx]

    def _run(self, dry, outdata):
        outdata.fill(0.0)
        if self.error is not None:
            return
        if self.reset_requested:
            self.reset_requested = False
            reset = getattr(self.processor, "reset", None)
            if reset is not None:
                reset()

        if self.bypass:
            wet = dry
        else:
            try:
                wet = self.processor.process(np.asarray(dry, dtype=np.float64))
            except Exception as e:  # report from the main thread, keep the stream silent
                self.error = e
                return

        wet = np.asarray(wet, dtype=np.float32)
        if wet.shape != dry.shape:
            self.error = ValueError(f"process() returned shape {wet.shape} for a block of {dry.shape}")
            return
        wet = np.nan_to_num(wet, nan=0.0, posinf=0.0, neginf=0.0)  # never send NaN to the speakers

        for ch in self.out_channels:
            if ch < outdata.shape[1]:
                outdata[:, ch] = wet
        self._record(dry, wet)
        self.blocks += 1

    def _record(self, dry, wet):
        space = len(self.dry) - self.recorded
        if space <= 0:
            return
        n = min(space, len(dry))
        self.dry[self.recorded : self.recorded + n] = dry[:n]
        self.wet[self.recorded : self.recorded + n] = wet[:n]
        self.recorded += n
