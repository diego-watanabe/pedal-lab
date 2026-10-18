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
bass → splitter ─┬─→ Babyface input 1           (dry, saved in di/)
                 └─→ pedal → Babyface input 2   (saved in pedal/)
```

- Record both inputs at once, so the dry and pedal files are the same
  performance and already line up.
- The dry file is what every simulation runs on (`run.py`); the pedal
  file is what the simulation is checked against.
- One take per pedal setting you want to compare.
- 48 kHz, 24-bit or 32-bit float, mono.
- Same input gain on both channels, and the same for every take.
- Bypass anything else in the chain (no Tonehammer).

## Naming

`<source>_<content>.wav` for DI files, and the same name plus the pedal and
its settings for the processed files:

```
di/stingray-active_low-e-sustain.wav
pedal/stingray-active_low-e-sustain__octabvre-mini_mix-max_tone-min_vol-noon.wav
```

Take a photo of the knobs for each setting and keep it next to the file.

## Test set ideas

- Active StingRay: main reference (low E and B notes, fast lines, double stops)
- P-bass: strong fundamental, easy tracking
- Fretless Big Al: slides, wide vibrato, the "mwah"
- Synthetic: sines at several pitches and levels, slow decays, sweeps
  (generate with `python/dsplab/signals.py`)
