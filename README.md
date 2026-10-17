# pedal-lab

Modeling guitar and bass pedals as audio plugins: prototype the DSP in
Python, port it to a plain C++ library, wrap it as JUCE plugins (VST3, AU on
macOS, standalone), and check every step against recordings of the real
pedals.

First targets: a ProCo RAT and a 3Leaf Audio Octabvre (OC-2 style octaver).

```
python/        prototypes and experiments (numpy/scipy), the reference implementation
dsp/           C++20 DSP library, no JUCE, real-time safe
plugins/       JUCE plugin wrappers (LabGain is the template)
tests/cpp/     Catch2 tests, including C++ vs Python reference tests
captures/      DI and reamped recordings of the real gear (audio not in git)
docs/          development guide and C++ standard
cmake/         warnings, sanitizers, pinned dependencies
```

## Documentation

- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**: setting up Windows or
  macOS, the test environment, and the step-by-step process from Python
  prototype to tested C++ and plugin, with a worked example.
- **[docs/CODE_TOUR.md](docs/CODE_TOUR.md)**: what every file does, and
  how a built plugin gets from the build folder to your bass and headphones.
- **[docs/CPP_STANDARDS.md](docs/CPP_STANDARDS.md)**: the C++ coding
  standard and review checklist.
- **[captures/README.md](captures/README.md)**: recording and reamping real
  gear.
- **[CLAUDE.md](CLAUDE.md)**: rules for AI assistants working in this repo.

## Quick start

After setting up your machine (see the development guide):

```sh
cd python && pytest && python run.py 01 && cd ..
cd python && python live.py --list-devices && cd ..   # then play: python live.py dc_blocker --device Babyface
cmake --preset dev && cmake --build --preset dev && ctest --preset dev
```

## Python exercises

`python/experiments/` holds eight exercises, in order: gain (done, the
template), hard clip, asymmetric clip, rectifier, aliasing, flip-flop
divider, one-pole low-pass, intermodulation. Each docstring states a
prediction and `pytest` checks it. `python/experiments/examples/` holds
complete worked examples.

## Versions

JUCE 9.0.3 and Catch2 3.16.0, pinned in `cmake/Dependencies.cmake`.
CI (`.github/workflows/ci.yml`) runs every check on Linux for each push and
pull request, and builds on Windows and macOS on `main`.
