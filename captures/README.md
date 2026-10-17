# Captures

Recordings of real gear, used as ground truth for the models. Audio files in
this folder are ignored by git (they get large); this README and any notes
are tracked.

```
captures/
├── di/      dry DI recordings: the reference inputs
└── pedal/   the same DI reamped through the real pedal
```

## Recording setup

```
Babyface line out → reamp box → pedal → Babyface instrument (Hi-Z) input
```

- 48 kHz, 24-bit or 32-bit float, mono.
- Start every file with an alignment click so input and output can be lined
  up exactly, cancelling the interface's round-trip latency.
- Keep the input gain the same as when the DI was recorded.
- Bypass anything else in the chain (no Tonehammer).

## Naming

`<source>_<content>.wav` for DI files, and the same name plus the pedal and
its settings for the processed files:

```
di/stingray-active_low-e-sustain.wav
pedal/stingray-active_low-e-sustain__octabvre_dry0-sub1max-sub2off.wav
```

Take a photo of the knobs for each setting and keep it next to the file.

## Test set ideas

- Active StingRay: main reference (low E and B notes, fast lines, double stops)
- P-bass: strong fundamental, easy tracking
- Fretless Big Al: slides, wide vibrato, the "mwah"
- Synthetic: sines at several pitches and levels, slow decays, sweeps
  (generate with `python/dsplab/signals.py`)
