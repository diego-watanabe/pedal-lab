# Code tour

What every file in pedal-lab does, how the pieces connect, and how a built
plugin ends up between your bass and your ears. Read alongside the code;
file paths are relative to the repo root.

---

## 1. The map

```
            Python side (prototyping)                  C++ side (the product)
 ┌──────────────────────────────────────┐   ┌─────────────────────────────────────┐
 │ dsplab/signals.py    test signals     │   │ dsp/include/pedallab/              │
 │ dsplab/analysis.py   measure, plot    │   │   Realtime.h   audio-thread marker │
 │ dsplab/wavio.py      WAV files        │   │   Gain.h       example processor   │
 │ dsplab/experiment.py load experiments │   │   DcBlocker.h  example processor   │
 │ dsplab/live.py       real-time engine │   │         ▲                ▲          │
 │                                       │   │         │ used by        │ used by  │
 │ run.py      render + measure          │   │ plugins/LabGain    tests/cpp/       │
 │ live.py     play through it           │   │ (JUCE wrapper)     (Catch2 tests)   │
 │ export_reference.py ───────────────────────────────────────►  reference/*.wav  │
 │                                       │   │                                     │
 │ experiments/  your algorithms         │   │ cmake/, CMakeLists.txt, presets     │
 │ tests/        predictions as tests    │   │ build system                        │
 └──────────────────────────────────────┘   └─────────────────────────────────────┘
```

The only bridge between the two sides is the reference WAV files: Python
writes them, C++ tests read them.

---

## 2. Python side

### `python/dsplab/signals.py`: test signals

Functions that return numpy arrays of samples: `sine`, `saw`, `square`,
`triangle`, `sweep` (exponential, for measuring across frequencies),
`impulse`, `noise`, plus helpers `decay` (exponential fade, like a plucked
note) and `mix`. Amplitudes are linear, 1.0 = digital full scale.

`parse()` turns short text specs into signals so you can choose inputs from
the command line: `"sine:110@0.5+dc@0.3"` means a 110 Hz sine at half scale
plus a constant 0.3 offset. Each `+` term is built by `_term()` and summed.

### `python/dsplab/analysis.py`: measuring

- `spectrum(x, sr)`: windowed FFT in dBFS, scaled so a full-scale sine reads
  0 dB. With 1 s of audio the bins are exactly 1 Hz apart, which is why most
  tests use 1-second signals and integer frequencies.
- `level_at(x, sr, freq)`: level of one frequency, the workhorse of the
  tests ("is there energy at 55 Hz?").
- `peaks()`: the strongest spectral peaks, refined with parabolic
  interpolation for sub-bin frequency accuracy.
- `peak_db`, `rms_db`, `dc_db`: overall levels.
- `report()` prints all of the above; `plot()` saves the 2x2 figure of
  waveforms and spectra.

### `python/dsplab/wavio.py`: WAV files

Reads and writes 32-bit float WAVs, so levels above full scale survive and
nothing is rounded to 16 or 24 bits. `read()` converts integer WAVs (from your
interface, say) to floats in -1..1 and mixes stereo to mono.

### `python/dsplab/experiment.py`: loading experiments

- `load("06")` finds `experiments/06_*.py` (by prefix, including the
  `examples/` folder) and imports it from its file path.
- `make_processor(module, sr)` gives `live.py` something it can call block by
  block: the module's `Processor` class if it has one; a wrapper around
  `process()` if the module says `STATELESS = True`; otherwise an error,
  because calling a stateful `process()` per block would reset its state
  every block.

### `python/dsplab/live.py`: the real-time engine

`LiveEngine` sits between the audio stream and your processor:

- `callback(indata, outdata, ...)` is what sounddevice calls for every block
  from the interface: take the input channel, run `processor.process()`,
  copy the result to the output channels, record both.
- `output_callback` does the same with a looping WAV as the input.
- `bypass` and `reset_requested` are flags the keyboard thread flips; the
  audio callback reads them at the start of the next block.
- Errors in your processor don't crash the stream: the engine goes silent
  and stores the exception for the main thread to report.
- Non-finite samples (NaN, infinity) are replaced with silence before they
  reach the outputs.
- Recording writes into arrays allocated up front, so the callback doesn't
  grow lists while audio is running.

It has no dependency on the audio library, which is why
`python/tests/test_live.py` can test it with fake buffers.

### `python/run.py`: render and measure

Loads an experiment, builds the input (from `--signal`, `--input`, or the
experiment's `SIGNAL`), calls `process(x, sr)` once on the whole signal, and
writes `renders/<experiment>/{input,output}.wav` and `plot.png`, then prints
the report.

### `python/live.py`: play through it

The command-line front end for `LiveEngine`: picks the audio device, opens a
duplex stream (input and output at once) or an output-only stream for
`--file`, compiles the experiment's numba code by running one silent block
before the stream starts, disables Python's garbage collector while audio
runs, prints CPU load and dropouts, and saves the recording on exit.

### `python/export_reference.py`: the bridge to C++

Generates the experiment's test signal, rounds it to float32 (the format C++
will read), runs `process()`, and writes `tests/cpp/reference/<name>/` with
`input.wav`, `output.wav` and `meta.json`.

### `python/experiments/`: the algorithms

Each file is one idea: module-level constants (parameters, `SIGNAL`, plot
settings), a docstring with the math and predictions, and `process(x, sr)`.
`01_gain.py` is complete; `02` to `08` are your exercises.
`examples/dc_blocker.py` shows the full pattern for stateful algorithms: a
numba-compiled `_kernel`, a `Processor` class holding state between blocks,
and `process()` built on top of it.

### `python/tests/`

- `test_experiments.py`: one test per exercise prediction. Unimplemented
  exercises raise `NotImplementedError`, which the `run()` helper turns into
  a skip.
- `test_examples.py`: the DC blocker's predictions.
- `test_live.py`: the live engine with fake buffers, including the key
  property that block-by-block output equals whole-signal output.

---

## 3. C++ DSP library: `dsp/`

Header-only: the code is entirely in `.h` files, so there's nothing to
compile until something includes them. `dsp/CMakeLists.txt` declares it as
an `INTERFACE` library, which in CMake means "a set of include paths and
settings that targets using me inherit".

### `Realtime.h`

Defines `PEDALLAB_NONBLOCKING`. With Clang 20+ it becomes
`[[clang::nonblocking]]`, a promise the compiler and the realtime sanitizer
check: no allocation, locks or system calls inside. With other compilers it
expands to nothing. It's the only macro in the library.

### `Gain.h`

The template every processor copies:

- `prepare(sampleRate)`: called before audio starts, when the sample rate is
  known. Converts the 20 ms ramp time to a number of samples.
- `reset()`: clears state. For Gain, jumps straight to the target gain.
- `setGainLinear()` / `setGainDecibels()`: set a new target and start a
  ramp: `step` is how much the gain changes per sample, `remaining` how many
  samples are left. Cheap enough to call every block.
- `process(std::span<float> block)`: the audio work. `std::span` is a view
  of someone else's array (a pointer plus a length) that works with
  range-for loops. Each sample is multiplied by the current gain, which moves
  one `step` closer to the target while a ramp is running.
- Members are plain floats and ints held by value: no pointers, no heap, no
  destructor needed.

### `DcBlocker.h`

The same shape, with state that must survive between blocks:
`previousInput` and `previousOutput` are members, so the filter's memory
carries over from one `process()` call to the next. Coefficients are
computed in `updateCoefficients()` (from `prepare()` and `setCutoffHz()`),
never per sample. Coefficients and state are `double`; samples are `float`,
converted explicitly with `static_cast`.

---

## 4. C++ tests: `tests/cpp/`

- `CMakeLists.txt`: builds one test program, `pedallab_tests`, from all the
  `test_*.cpp` files, linked with the DSP library, the strict warnings and
  Catch2. `catch_discover_tests()` registers each test case with CTest, which
  is what `ctest --preset dev -R DcBlocker` filters on. It also passes
  `PEDALLAB_REFERENCE_DIR` so tests can find the reference WAVs.
- `WavFile.h`: a small WAV reader (16, 24 and 32-bit integer and 32-bit
  float). Test-only, so it may allocate and throw.
- `Reference.h`: `loadReference()` reads a reference folder;
  `checkMatches()` compares two sample arrays and reports the worst sample.
- `TestSignals.h`: `sine()` for C++ tests that need a test tone.
- `test_gain.cpp`, `test_dc_blocker.cpp`: each `TEST_CASE` is one property.
  `CHECK(...)` records a failure and continues; `REQUIRE(...)` stops the
  test case. `Approx(x).epsilon(e)` compares floats with a relative
  tolerance.

---

## 5. The plugin: `plugins/LabGain/`

A plugin is a class derived from `juce::AudioProcessor`. The host (your DAW,
or the standalone app) creates it and calls its methods; JUCE translates
between that class and each plugin format's own API (VST3, AU, ...).

### `PluginProcessor.h` / `PluginProcessor.cpp`

In the order a host uses them:

1. **`createPluginFilter()`** (bottom of the .cpp): the factory function the
   host calls to create an instance. One of the two places `new` is allowed.
2. **Constructor**: declares the audio buses (stereo in, stereo out) and
   creates `parameters`, an `AudioProcessorValueTreeState` (APVTS) built
   from `createLayout()`. The APVTS is JUCE's parameter manager: it exposes
   parameters to the host for automation, stores them for saving, and keeps
   each value in a `std::atomic<float>` that the audio thread can read
   without locks. `gainDb` is a pointer to that atomic.
3. **`isBusesLayoutSupported()`**: the host asks "can you do mono? stereo?
   5.1?"; this says mono or stereo, with matching input and output.
4. **`prepareToPlay(sampleRate, maxBlockSize)`**: called before audio
   starts, and again whenever the sample rate or buffer size changes. Calls
   `prepare()` on each channel's `pedallab::Gain`.
5. **`processBlock(buffer, midi)`**: called on the audio thread for every
   block, typically 64 to 512 samples, hundreds of times a second.
   `ScopedNoDenormals` switches the CPU to flush tiny numbers to zero for the
   duration of the block (denormals are very slow on x86). The current gain
   is read once from the atomic, then each channel's samples are wrapped in a
   `std::span` and handed to the DSP library. The plugin does no audio math
   itself.
6. **`getStateInformation()` / `setStateInformation()`**: save and restore
   parameter values when you save and reopen a DAW project, via XML.
7. **`createEditor()`**: the plugin's window. `GenericAudioProcessorEditor`
   draws a slider per parameter automatically; a custom UI replaces it later.

The remaining overrides (`getName`, `acceptsMidi`, programs...) are required
by the base class and return fixed answers.

### `plugins/LabGain/CMakeLists.txt` and `plugins/CMakeLists.txt`

`juce_add_plugin()` creates the build targets: one shared-code library
holding your processor, plus one thin wrapper target per format
(`LabGain_VST3`, `LabGain_Standalone`, `LabGain_AU` on macOS). The shared
settings (company name, formats, copying to the plugin folder) live in
`PEDALLAB_PLUGIN_COMMON_ARGS` in `plugins/CMakeLists.txt`. `PLUGIN_CODE` and
`BUNDLE_ID` identify the plugin to hosts; they must be unique per plugin and
must not change once you use it in projects, or the DAW won't find it.

---

## 6. Build system and tooling

- **`CMakeLists.txt`**: the project root. Sets C++20, declares the options
  (`PEDALLAB_BUILD_PLUGINS`, `PEDALLAB_BUILD_TESTS`, `PEDALLAB_SANITIZER`),
  includes the helpers in `cmake/`, and adds `dsp`, `plugins` and
  `tests/cpp`.
- **`cmake/Dependencies.cmake`**: downloads JUCE and Catch2 at exact
  versions. `SYSTEM` marks JUCE's headers so our strict warnings don't apply
  to its code.
- **`cmake/Warnings.cmake`**: the warning flags; `pedallab_warn()` applies
  them to individual files in targets that also compile JUCE sources.
- **`cmake/Sanitizers.cmake`**: compiler flags for each sanitizer preset.
- **`CMakePresets.json`**: named configurations (`dev`, `release`, `dsp`,
  `asan`, ...), each with its own folder under `build/`, so
  `cmake --preset asan` replaces a long command line.
- **`.clang-format`**, **`.clang-tidy`**: layout and lint rules (see
  `docs/CPP_STANDARDS.md`).
- **`.github/workflows/ci.yml`**: runs everything on GitHub for each push.

---

## 7. From a built plugin to playing your bass through it

### What a "plugin" actually is

A plugin is a library: compiled code with no `main()`, which can't run by
itself. Building the VST3 target produces a folder named
`Lab Gain.vst3`. Inside it, under `Contents/x86_64-win/` on Windows (or
`Contents/MacOS/` on a Mac), is the actual compiled library. A **host**
loads that library, creates your processor through `createPluginFilter()`,
and from then on calls `processBlock()` with audio.

The host is the program that owns the audio interface. Your code never opens
the Babyface itself. That's the division of labor that lets one plugin run in
any DAW: the host deals with drivers, routing and recording; the plugin just
turns blocks of samples into other blocks of samples.

### The signal path

```
bass ─► Babyface Hi-Z input ─► analog-to-digital converter
     ─► ASIO driver ─► host (DAW or standalone app)
     ─► your processBlock(): 128 samples at a time
     ─► host ─► ASIO driver ─► digital-to-analog converter
     ─► headphones or amp
```

Each step adds a little latency. With a 128-sample buffer at 48 kHz, one
block is 2.7 ms; the round trip including converters is typically 5 to 8 ms
on a Babyface, which feels immediate to most players. Larger buffers are
safer for CPU but add delay you'll feel.

### Way 1: the standalone app (simplest)

JUCE also builds every plugin as a normal application, the
`LabGain_Standalone` target. It hosts your processor itself, no DAW needed.

1. Run `build/dev/plugins/LabGain/LabGain_artefacts/Debug/Standalone/Lab Gain.exe`.
2. Open **Options → Audio/MIDI Settings**. Choose the ASIO driver for the
   Babyface, select the input your bass is on, set the outputs to your
   headphones, and pick the buffer size.
3. JUCE mutes the input by default to avoid feedback (a microphone near
   speakers would howl). With a bass plugged in there's no acoustic loop,
   so turn **Mute audio input** off in the same settings window.
4. Play. The slider is the gain parameter.

This is the quickest way to try a change: rebuild, relaunch, play.

### Way 2: inside a DAW (Reaper, for example)

1. Building copies `Lab Gain.vst3` to your per-user VST3 folder
   (`%LOCALAPPDATA%\Programs\Common\VST3` on Windows,
   `~/Library/Audio/Plug-Ins/VST3` on a Mac). Make sure the DAW scans that
   folder, then rescan.
2. Set the DAW's audio device to the Babyface's ASIO driver.
3. Make a track, set its input to the Babyface input your bass is on,
   arm it for recording and turn input monitoring on.
4. Add **Lab Gain** to the track's effects. Play: you hear your bass through
   the plugin, live.

This is how you'll use the finished pedals: stack them on a track (octaver
into RAT), automate knobs, record. It's also where pluginval-style problems
show up for real, like how the plugin behaves when you change buffer sizes
or reopen a project.

DAWs often keep a plugin's library loaded until they restart, so after a
rebuild you may need to close and reopen the DAW (or the project) to get the
new version.

### Way 3: other devices, later

The same processor code becomes an AUv3 for iPhone and iPad (via an
interface like an iRig into GarageBand or AUM), or a WebAssembly demo in a
browser, by adding other wrappers around the same `dsp/` library. That's why
the DSP has no JUCE dependency.

### Sharing a plugin with someone else

For another Windows machine, copying the `Lab Gain.vst3` folder from a
`release` build into their VST3 folder is enough. Distributing more widely
means an installer and code signing (and on macOS, Apple notarization), a
separate topic for when you have something worth sharing.
