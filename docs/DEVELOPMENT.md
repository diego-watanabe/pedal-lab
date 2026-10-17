# Development guide

How to set up a machine for pedal-lab, what the test environment checks, and
the step-by-step process for taking an idea from a Python prototype to a
tested C++ processor and plugin.

Related documents:
- `docs/CPP_STANDARDS.md`: the C++ coding standard and review checklist
- `captures/README.md`: recording DI and reamped captures of real gear
- `CLAUDE.md`: rules for AI assistants working in this repo

---

## 1. The pipeline at a glance

```
 idea / circuit
      │
      ▼
 ① Python experiment        python/experiments/…           you write this
      │  run.py: listen, plot, measure
      ▼
 ② Python tests             python/tests/…                 predictions as code
      │
      ▼
 ③ Reference export         tests/cpp/reference/<name>/    input.wav + output.wav
      │
      ▼
 ④ C++ processor            dsp/include/pedallab/…         AI writes, you review
      │
      ▼
 ⑤ C++ tests                tests/cpp/…                    contract + reference
      │  sanitizers, clang-tidy, warnings as errors
      ▼
 ⑥ Plugin wrapper           plugins/<Name>/                parameters + channels
      │  pluginval
      ▼
 ⑦ Compare with real gear   captures/                      reamped recordings
```

Each stage checks the one before it. The Python prototype is the reference:
if the C++ disagrees with it, the C++ is wrong until proven otherwise.

---

## 2. Setting up a machine

### 2.1 Windows

1. **Git for Windows** (https://git-scm.com). Accept the default of checking
   out with LF line endings preserved; the repo's `.gitattributes` handles it.

2. **Visual Studio 2022 Community** (https://visualstudio.microsoft.com).
   In the installer, select the **Desktop development with C++** workload,
   and under its optional components make sure these are ticked:
   - C++ CMake tools for Windows (installs CMake and Ninja)
   - C++ Clang tools for Windows (installs clang-format and clang-tidy)

3. **Python.** You have Anaconda, so a conda environment is the easiest
   route. From the Anaconda Prompt:
   ```bat
   conda create -n pedal-lab python=3.12
   conda activate pedal-lab
   cd path\to\pedal-lab\python
   pip install -r requirements.txt
   ```
   Run `conda activate pedal-lab` in each new terminal before using Python.
   (A python.org install with `py -3.12 -m venv .venv` and
   `.venv\Scripts\activate` works too.)

4. **Build tools in a terminal.** C++ builds must run in a terminal where
   Visual Studio's compiler is set up for 64-bit. Use the Start menu entry
   **x64 Native Tools Command Prompt for VS 2022**. Check with `cl`; the first
   line must end in `for x64`. (The plain "Developer PowerShell" defaults to
   32-bit on some installs, which builds plugins most DAWs can't load.)

5. **Audio.** Install RME's ASIO driver for the Babyface (from rme-audio.de).
   For a test host, Reaper is a good choice: inexpensive, loads VST3, and fast
   to rescan. Built plugins are copied to the per-user VST3 folder,
   `%LOCALAPPDATA%\Programs\Common\VST3`. Some DAWs don't scan it by default;
   in Reaper, add it under Preferences → Plug-ins → VST.

**Windows limitations:** no AU plugins (Apple-only), and of the sanitizers
only AddressSanitizer runs locally. UndefinedBehavior, Thread and Realtime
sanitizers run in CI on Linux.

**Editors:** Visual Studio can open the repo folder directly
(File → Open → Folder), reads `CMakePresets.json`, and lets you pick the
`dev` preset and debug the standalone app. VS Code with the CMake Tools
extension works the same way.

### 2.2 macOS

1. **Xcode** from the App Store (needed for AU plugins and debugging). Open it
   once to accept the license.
2. **Homebrew tools:**
   ```sh
   brew install cmake ninja llvm python@3.12
   ```
   `llvm` provides clang-format, clang-tidy and a Clang new enough for the
   realtime sanitizer. Add it to the end of your PATH in `~/.zshrc` so Apple's
   compiler stays the default for normal builds:
   ```sh
   export PATH="$PATH:$(brew --prefix llvm)/bin"
   ```
3. **Python:**
   ```sh
   cd python
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Audio:** the Babyface works class-compliant or with RME's driver.
   Plugins are copied to `~/Library/Audio/Plug-Ins/{VST3,Components}`.
   For debugging inside a host, `cmake --preset xcode` generates
   `build/xcode/pedal-lab.xcodeproj`.

### 2.3 Check the setup

From the repo root (on Windows, in the x64 Native Tools prompt with the conda
environment active):

```sh
cd python
pytest                    # expect: 3 passed, 9 skipped
python run.py 01          # writes python/renders/01_gain/
cd ..
cmake --preset dev        # first run downloads JUCE and Catch2: a few minutes
cmake --build --preset dev
ctest --preset dev        # expect: 100% tests passed
```

Then rescan plugins in your DAW: **Lab Gain** should appear. The standalone
app is in `build/dev/plugins/LabGain/LabGain_artefacts/Debug/Standalone/`.

If `cmake --preset dev` fails with "Ninja not found" or "No CMAKE_CXX_COMPILER",
the terminal isn't set up for Visual Studio (Windows) or the Xcode command
line tools aren't installed (macOS).

---

## 3. The test environment

Seven layers, each catching a different kind of mistake.

| Layer | Catches | Command | When |
| --- | --- | --- | --- |
| Python tests | the algorithm doesn't do what you predicted | `cd python && pytest` | while prototyping |
| C++ unit tests | the processor breaks its contract (reset, block size, gain) | `ctest --preset dev` | every build |
| Reference tests | the C++ doesn't match the Python prototype | `ctest --preset dev` | every build |
| Compiler warnings as errors | implicit conversions, shadowing, C-style casts | `cmake --build --preset dev` | every build |
| clang-tidy and clang-format | ownership mistakes, naming, non-modern idioms, layout | `clang-tidy -p build/dev <file>`, `clang-format --dry-run --Werror <file>` | before committing |
| Sanitizers | memory errors, undefined behavior, data races, real-time violations | `asan`, `ubsan`, `tsan`, `rtsan` presets | before committing; all in CI |
| pluginval | the plugin misbehaves under host-like stress | CI, or run pluginval locally | when plugin code changes |

The eighth layer is you: listening, and comparing against captures of the
real pedal (section 4, step 9). No automated test tells you whether it sounds
like a RAT.

### 3.1 Running tests

```sh
ctest --preset dev                       # all C++ tests
ctest --preset dev -R DcBlocker          # tests whose name contains "DcBlocker"
build/dev/tests/cpp/pedallab_tests "[reference]"   # by Catch2 tag
cd python && pytest -k divider           # Python tests matching "divider"
```

Sanitizer runs use their own build folders, so they don't disturb `dev`:

```sh
cmake --preset asan && cmake --build --preset asan && ctest --preset asan
```

The `rtsan` preset needs Clang 20 or newer. On macOS:
`CC=$(brew --prefix llvm)/bin/clang CXX=$(brew --prefix llvm)/bin/clang++ cmake --preset rtsan`.

### 3.2 How reference tests work

1. `python export_reference.py <experiment>` generates the experiment's test
   signal (0.25 s by default), runs the Python `process()`, and writes
   `tests/cpp/reference/<experiment>/input.wav`, `output.wav` (32-bit float)
   and `meta.json` (which signal and settings produced them). These files are
   committed; they are small.
2. A C++ test loads them with `pedallab::test::loadReference("<experiment>")`,
   runs `input` through the C++ processor, and calls
   `pedallab::test::checkMatches(actual, expected, tolerance)`.
3. On failure, the message names the worst sample:
   ```
   worst error 0.115455 at sample 207: got 0.113808, expected 0.229264
   ```
   (That one came from setting the C++ cutoff to 20 Hz while the Python used
   10 Hz.)

**Choosing a tolerance.** Start tight and loosen only with a reason you can
write in a comment next to the test:

| Situation | Typical tolerance |
| --- | --- |
| Same math, same precision (gain, clipping) | `1e-6f` |
| C++ keeps state in float, Python in double | `1e-5f` to `1e-4f` |
| Different but equivalent formulations (rearranged filter equations) | `1e-4f` |
| Deliberately different algorithms (oversampled vs not) | don't compare samples; compare spectra or levels |

**Regenerate a reference** whenever the Python prototype changes. The C++
test then fails until the C++ catches up, which is the point.

---

## 4. From prototype to C++: the process

This walks through the DC blocker, a small filter that removes DC offset,
already in the repo as a complete example:

- `python/experiments/examples/dc_blocker.py`: the prototype
- `python/tests/test_examples.py`: its Python tests
- `tests/cpp/reference/dc_blocker/`: the exported reference
- `dsp/include/pedallab/DcBlocker.h`: the C++ processor
- `tests/cpp/test_dc_blocker.cpp`: its C++ tests

It's a good template because it has state (its previous input and output),
which is where most porting bugs live. The gain example has none.

### Step 1: Write the experiment

Create a file in `python/experiments/` with a `process(x, sr)` function.
Conventions that make the later port straightforward:

- **The docstring states the math and the predictions.** Write the equation
  you're implementing and what you expect to see before running anything.
  ```
  y[n] = g * (x[n] - x[n-1]) + R * y[n-1]
  Predictions: the 0.3 DC offset is gone once the filter settles;
               the 110 Hz tone passes within 0.05 dB.
  ```
- **Parameters are module-level constants with units in the name**
  (`CUTOFF_HZ = 10.0`). They become C++ setters (`setCutoffHz`).
- **Set `SIGNAL`** to an input that exercises the behavior. For the DC blocker
  that's a tone plus an offset: `"sine:110@0.5+dc@0.3"`.
- **Stateful algorithms are explicit per-sample loops with named state.**
  It's slower in Python than vectorized numpy, but it maps line for line
  onto C++:
  ```python
  x1 = 0.0
  y1 = 0.0
  for n in range(len(x)):
      y1 = g * (x[n] - x1) + R * y1
      x1 = x[n]
      y[n] = y1
  ```
  Stateless operations (clipping, `abs`, gain) can stay vectorized.

### Step 2: Run it, look at it, listen to it

```sh
cd python
python run.py dc_blocker
```

This writes `python/renders/dc_blocker/` with `input.wav`, `output.wav` and
`plot.png` (waveforms and spectra), and prints peak, RMS and DC levels plus
the strongest spectral peaks. Check that the plot and numbers match the
predictions in your docstring. Listen to `output.wav`. Try other inputs:
`--signal "decay:sine:41.2"` for a fading low E, `--input` with a real DI.

### Step 3: Turn the predictions into tests

Add tests to `python/tests/` that check each prediction numerically:

```python
def test_dc_blocker_removes_offset():
    mod = experiment.load("dc_blocker")
    x = signals.parse("sine:110@0.5+dc@0.3", 1.0, SR)
    y = mod.process(x.copy(), SR)
    assert abs(np.mean(y[SR // 2 :])) < 1e-4
```

Now the prototype is pinned down. If you change it later and break a
prediction, `pytest` tells you.

### Step 4: Export the reference

```sh
python export_reference.py dc_blocker
```

Pick a signal that covers the interesting behavior, including the start-up
transient: the first few milliseconds are where state bugs show. Keep it short
(the 0.25 s default is usually enough). Commit the files.

### Step 5: Write the C++ processor

Add `dsp/include/pedallab/<Name>.h` following `Gain.h` and `DcBlocker.h`, and
the rules in `docs/CPP_STANDARDS.md`. The translation is mostly mechanical:

| Python prototype | C++ processor |
| --- | --- |
| module constant `CUTOFF_HZ = 10.0` | member `cutoffHz` with `setCutoffHz()` |
| coefficient computed from `sr` (`R = np.exp(...)`) | computed in `prepare()` / `updateCoefficients()`, never per sample |
| local state (`x1`, `y1`) | members (`previousInput`, `previousOutput`), cleared in `reset()` |
| the loop body | the body of `process(std::span<float>)` |
| float64 everywhere | `float` samples; `double` for coefficients and sensitive state |
| fixed `sr = 48000` | whatever sample rate `prepare()` receives |
| a constant knob | a parameter that can change mid-stream: smooth it if it changes gain or filter coefficients |

The header comment names the source of the math (the Python file, a paper,
a schematic) and states how aliasing is handled.

### Step 6: Write the C++ tests

In `tests/cpp/test_<name>.cpp` (and add the file to
`tests/cpp/CMakeLists.txt`):

1. **Contract tests** every processor gets:
   - behaves as expected on simple input (DC removed, tone passes)
   - `reset()` clears state
   - output doesn't depend on block size (process in blocks of 1, 7, 64, 512
     and compare against one big block)
2. **The reference test:**
   ```cpp
   const auto ref = pedallab::test::loadReference("dc_blocker");
   pedallab::DcBlocker blocker;
   blocker.prepare(ref.sampleRate);
   blocker.setCutoffHz(10.0); // must match CUTOFF_HZ in dc_blocker.py
   auto block = ref.input;
   blocker.process(block);
   pedallab::test::checkMatches(block, ref.output, 1e-6f);
   ```
   with a comment explaining the tolerance.

### Step 7: Run every check

```sh
cmake --build --preset dev && ctest --preset dev
cmake --preset asan && cmake --build --preset asan && ctest --preset asan
clang-tidy -p build/dev tests/cpp/test_<name>.cpp
clang-format --dry-run --Werror dsp/include/pedallab/<Name>.h tests/cpp/test_<name>.cpp
```

Then go through the review checklist at the end of `docs/CPP_STANDARDS.md`.

When the DC blocker was written for this guide, the build failed on the first
try: `-Wdouble-promotion` caught an implicit float-to-double conversion in
the inner loop. The fix was one `static_cast`, but that's the kind of thing
the checks exist to catch before it reaches a review.

### Step 8: Wrap it in a plugin

Only processors meant to be played through become plugins; building blocks
like the DC blocker are used inside other processors instead.

1. Copy `plugins/LabGain` to `plugins/<Name>`.
2. In its `CMakeLists.txt`, change the target name, `PRODUCT_NAME`,
   `BUNDLE_ID` and `PLUGIN_CODE` (four characters, at least one uppercase,
   unique within the project).
3. Add `add_subdirectory(<Name>)` to `plugins/CMakeLists.txt`.
4. In the processor class, declare parameters in `createLayout()`, read them
   with `getRawParameterValue()` (an atomic), and forward them to the DSP
   processor at the top of `processBlock()`. The plugin holds one DSP
   processor per channel; all sound-making code stays in `dsp/`.
5. Build, rescan in your DAW, try it. CI runs pluginval on it.

### Step 9: Compare with the real pedal

For pedal models: record DI and reamped captures as described in
`captures/README.md`, run the same DI through the Python model
(`python run.py <experiment> --input ../captures/di/<file>.wav`) and through
the plugin, and compare by ear and with spectra. Differences found here go
back to step 1: fix the prototype, regenerate the reference, and let the C++
tests drive the C++ fix.

### Common porting mistakes, and what catches them

Measured on the DC blocker:

| Mistake | Effect | Caught by |
| --- | --- | --- |
| State reset at the start of every block | worst error 0.34: a click every block | reference test, block-size test |
| Parameter differs between Python and C++ (20 Hz vs 10 Hz) | worst error 0.12 | reference test |
| State in float instead of double | worst error 8e-7 here; grows at lower cutoffs | reference test, if the tolerance is tight |
| Coefficient computed with a hard-coded 48000 | wrong cutoff at any other sample rate | a unit test at 44.1 or 96 kHz |
| Implicit float/double conversion | precision loss, slower code | `-Wdouble-promotion`, `-Wconversion` |
| Allocation in `process()` | dropouts under load | `rtsan` preset, review |

---

## 5. Porting with an AI assistant

The split that works: you write the Python prototype and its tests (that's
where the understanding happens), the AI writes the C++ and its tests, and
the reference test holds the C++ to your prototype.

A prompt that works well:

> Port `python/experiments/<file>.py` to a C++ processor in
> `dsp/include/pedallab/<Name>.h`, following `docs/CPP_STANDARDS.md` and the
> shape of `DcBlocker.h`. Export the reference with
> `python export_reference.py <experiment>` and add
> `tests/cpp/test_<name>.cpp` with the contract tests and a reference test,
> including a comment justifying the tolerance. Run the dev and asan builds,
> ctest, clang-tidy and clang-format, and go through the review checklist.
> Don't change anything under `python/experiments/` or `python/tests/`.

When reviewing the result:

- Read the reference test first: right experiment, same parameter values as
  the Python constants, a tolerance with a reason.
- Check that no test was loosened or deleted to make things pass.
- Go through the checklist at the end of `docs/CPP_STANDARDS.md`.
- Listen to it.

---

## 6. Quick reference

```sh
# Python
cd python
python run.py <experiment> [--signal SPEC] [--input FILE] [--duration S]
pytest [-k NAME]
python export_reference.py <experiment> [--signal SPEC] [--duration S]

# C++
cmake --preset dev && cmake --build --preset dev && ctest --preset dev
ctest --preset dev -R <TestName>
cmake --preset asan && cmake --build --preset asan && ctest --preset asan
clang-tidy -p build/dev <file.cpp>
clang-format -i <files>
```

Signal specs: `sine:110`, `saw:55`, `square:110`, `triangle:220`,
`sweep:20-20000`, `impulse`, `noise`, `dc`, `decay:sine:110`; amplitude with
`@0.5`; sums with `+`, as in `sine:110@0.5+dc@0.3`.
