# pedal-lab

Modeling guitar and bass pedals as audio plugins: prototype the DSP in
Python, port it to a plain C++ library, wrap it as JUCE plugins (AU, VST3,
standalone), and check every step against recordings of the real pedals.

First targets: a ProCo RAT and a 3Leaf Audio Octabvre (OC-2 style octaver).

```
python/        prototypes and experiments (numpy/scipy), the reference implementation
dsp/           C++20 DSP library, no JUCE, real-time safe
plugins/       JUCE plugin wrappers (LabGain is the template)
tests/cpp/     Catch2 tests, including C++ vs Python reference tests
captures/      DI and reamped recordings of the real gear (audio not in git)
cmake/         warnings, sanitizers, pinned dependencies
```

## Setup (macOS)

1. **Xcode** from the App Store (needed for AU plugins and debugging), then
   open it once to accept the license.
2. **Homebrew tools:**
   ```sh
   brew install cmake ninja llvm python@3.12
   ```
   `llvm` provides clang-format, clang-tidy and a Clang new enough for the
   realtime sanitizer. It is not put on your PATH by default; add this to
   `~/.zshrc` to use its clang-format and clang-tidy:
   ```sh
   export PATH="$PATH:$(brew --prefix llvm)/bin"
   ```
   (Appended, so Apple's compiler stays the default for normal builds.)
3. **Python environment:**
   ```sh
   cd python
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pytest            # 1 passed, the rest skipped until you write them
   ```
4. **C++ build** (the first configure downloads JUCE and Catch2, a few minutes):
   ```sh
   cmake --preset dev
   cmake --build --preset dev
   ctest --preset dev
   ```
   On macOS the built plugins are copied to `~/Library/Audio/Plug-Ins`, so
   "Lab Gain" shows up in your DAW after a rescan. The standalone app is in
   `build/dev/plugins/LabGain/LabGain_artefacts/Debug/Standalone/`.

For debugging a plugin inside a host, generate an Xcode project with
`cmake --preset xcode` and open `build/xcode/pedal-lab.xcodeproj`.

## Workflow

### 1. Prototype in Python

Each experiment in `python/experiments/` is a file with a
`process(x, sr)` function. Its docstring states a prediction, and
`python/tests/` checks it.

```sh
cd python
python run.py 01                                  # default signal (sine:110)
python run.py 02 --signal "sine:110@0.8"
python run.py 06 --signal "decay:sine:41.2" --duration 2
python run.py 06 --input ../captures/di/stingray-active_low-e-sustain.wav
pytest -k divider
```

`run.py` writes `input.wav`, `output.wav` and `plot.png` (waveforms and
spectra) to `python/renders/<experiment>/` and prints levels and the
strongest spectral peaks.

Signal specs: `sine:110`, `saw:55`, `square:110`, `triangle:220`,
`sweep:20-20000`, `impulse`, `noise`, `decay:sine:110`, amplitudes with
`@0.5`, sums with `+` (`sine:110@0.5+sine:165@0.5`).

Exercises, in order: gain (done, the template), hard clip, asymmetric clip,
rectifier, aliasing, flip-flop divider, one-pole low-pass, intermodulation.

### 2. Port to C++

Add a processor to `dsp/include/pedallab/` following `Gain.h`. Then export the
Python output as the reference and test against it:

```sh
cd python && python export_reference.py 06_divider
```

```cpp
const auto ref = pedallab::test::loadReference("06_divider");
// run ref.input through the C++ processor, then:
pedallab::test::checkMatches(output, ref.output, 1e-5f);
```

### 3. Wrap as a plugin

Copy `plugins/LabGain`, rename it, give it a new `PLUGIN_CODE` and
`BUNDLE_ID`, and add it to `plugins/CMakeLists.txt`. The plugin only handles
parameters and channels; the DSP stays in `dsp/`.

### 4. Compare with the real pedal

Record and reamp as described in `captures/README.md`, then run the same DI
through the Python model and the plugin and compare.

## Checks

| Command | What it catches |
| --- | --- |
| `cmake --preset dev` + build | warnings are errors for our code |
| `ctest --preset dev` | unit and reference tests |
| `cmake --preset asan` / `ubsan` / `tsan` + build + `ctest --preset ...` | memory bugs, undefined behavior, thread races |
| `cmake --preset rtsan` + build + `ctest --preset rtsan` | allocations or locks in `PEDALLAB_NONBLOCKING` code (needs Homebrew LLVM: `CC=$(brew --prefix llvm)/bin/clang CXX=$(brew --prefix llvm)/bin/clang++ cmake --preset rtsan`) |
| `clang-format`, `clang-tidy -p build/dev <file>` | style, common bug patterns |
| pluginval (in CI) | plugin behavior under host-like stress |

CI (`.github/workflows/ci.yml`) runs all of these on Linux for every push and
pull request, and builds and validates the AU and VST3 on macOS on `main`.

`CLAUDE.md` holds the rules for AI assistants working in this repo.

## Versions

JUCE 9.0.3 and Catch2 3.16.0, pinned in `cmake/Dependencies.cmake`.
