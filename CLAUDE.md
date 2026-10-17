# pedal-lab: rules for AI assistants

This repo models guitar/bass pedals (first a ProCo RAT and a 3Leaf Octabvre,
an OC-2-style octaver) as audio plugins. The owner writes the Python
prototypes to learn the DSP; AI assistants write most of the C++.
These rules are not optional. If a task seems to need breaking one, stop and
ask.

**Read `docs/CPP_STANDARDS.md` before writing any C++.** It is the full
standard (modern C++ idioms, naming, real-time rules, thread communication,
DSP conventions) and ends with a review checklist that every change must
pass. The sections below are the short version.

**`docs/DEVELOPMENT.md` section 4 is the process for porting a Python
prototype to C++.** Follow it step by step; `DcBlocker.h` and
`tests/cpp/test_dc_blocker.cpp` are the model to copy.

## Layout

- `python/` prototypes, experiments, analysis. The Python version of an
  algorithm is the reference the C++ must match.
- `dsp/include/pedallab/` the DSP library: plain C++20, header-only for now.
- `plugins/<Name>/` thin JUCE wrappers around `dsp/` processors.
- `tests/cpp/` Catch2 tests, including reference tests against Python output.
- `captures/` recordings of real gear (audio files are not in git).

## Real-time rules (audio thread)

Code reachable from `processBlock()` or any `process*()` method must not:

- allocate or free memory (`new`, `delete`, `std::vector` growth,
  `std::string`, `std::function` construction, `juce::String`, ...)
- take locks or wait (`std::mutex`, `juce::CriticalSection`, condition
  variables, `sleep`)
- do I/O or system calls (files, logging, `printf`, `DBG`)
- throw exceptions

Allocate in `prepare()`/`prepareToPlay()`. Pass values between threads with
`std::atomic` or lock-free FIFOs. Mark audio-thread functions with
`PEDALLAB_NONBLOCKING` (from `pedallab/Realtime.h`) so the realtime
sanitizer can check them.

## DSP library rules

- No JUCE includes anywhere under `dsp/`. Use the standard library only.
- Each processor follows the shape of `pedallab::Gain`: `prepare(sampleRate)`,
  `reset()`, setters, `process(std::span<float>)` marked `noexcept` and
  `PEDALLAB_NONBLOCKING`.
- Smooth any parameter that changes gain or filter coefficients.
- Use `float` for audio samples. Use `double` for coefficient math and long
  accumulators, then cast explicitly.

## Testing rules

- Every change to `dsp/` comes with tests in `tests/cpp/`.
- New processors get a reference test: export the Python prototype's output
  with `python/export_reference.py <experiment>` and compare against it with
  `pedallab::test::checkMatches`. State the tolerance and why.
- Never loosen a tolerance or delete a failing test to make CI pass. Find out
  why it fails, and ask if the Python reference itself looks wrong.
- Do not modify `python/experiments/` or `python/tests/` unless asked: those
  are the owner's learning exercises.

## Style and build

- C++20. Format with `.clang-format`; code must pass `.clang-tidy`.
- Warnings are errors for our code. Fix warnings; do not silence them with
  pragmas or by editing `cmake/Warnings.cmake` unless asked.
- Third-party code is pinned to exact versions in `cmake/Dependencies.cmake`.
  Ask before adding a dependency.
- Before finishing a task, run:
  ```
  cmake --preset dev && cmake --build --preset dev && ctest --preset dev
  cmake --preset asan && cmake --build --preset asan && ctest --preset asan
  cd python && pytest
  ```
