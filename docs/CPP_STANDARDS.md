# C++ standards for pedal-lab

These rules apply to everything under `dsp/`, `plugins/` and `tests/cpp/`.
Where a tool enforces a rule, the tool is listed; everything else is checked
in review.

**Precedence:** this document, then the JUCE coding standards (for naming and
layout), then the C++ Core Guidelines (for everything else).

- C++ Core Guidelines: https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
- JUCE coding standards: https://juce.com/discover/stories/coding-standards
- Real-time audio background: Ross Bencina, "Real-time audio programming 101:
  time waits for nothing"; Timur Doumler's talks on lock-free programming and
  on using the standard library for real-time audio; Fabian Renn-Giles and
  Dave Rowland, "Real-time 101" (ADC 2019).

---

## 1. Modern C++ for someone who knows classic OOP

Modern C++ keeps classes but leans on a few ideas that change how they are
used. These matter more than any formatting rule.

**Value semantics.** Objects behave like `int`s: they are copied, moved and
destroyed automatically. Prefer members held by value (`Gain gain;`) over
pointers to heap objects (`Gain* gain = new Gain;`). A DSP processor is a
plain value: a few floats of state and some methods.

**RAII and the rule of zero.** Resources (memory, files, locks) are owned by
objects whose destructors release them. If every member manages itself
(`std::vector`, `std::unique_ptr`, `std::array`), your class needs no
destructor, copy constructor or assignment operator at all. Write none of
them unless the class owns a raw resource directly, which should be rare.
(Core Guidelines C.20, R.1)

**No `new` or `delete` in our code.** Use members by value, standard
containers, or `std::make_unique`. JUCE's API sometimes returns raw pointers
it expects the host to own (`createEditor()`, `createPluginFilter()`); those
are the only `new` expressions allowed. (JUCE standard; clang-tidy
`cppcoreguidelines-owning-memory` is off only for those JUCE entry points.)

**Composition over inheritance.** Build a RAT out of a `GainStage`, a
`DiodeClipper` and a `ToneFilter` held as members, not as a class hierarchy.
Use inheritance only where a framework requires it (`juce::AudioProcessor`)
or for a genuine "is-a" interface used polymorphically outside the audio loop.

**No virtual calls per sample.** A virtual call in an inner loop blocks
inlining and costs far more than the arithmetic it wraps. When processors
need to be interchangeable, use templates (static polymorphism), constrained
with C++20 concepts so errors are readable:

```cpp
template <typename Processor>
concept MonoProcessor = requires(Processor p, std::span<float> block, double sampleRate) {
    p.prepare(sampleRate);
    p.reset();
    p.process(block);
};

template <MonoProcessor First, MonoProcessor Second>
class Chain { First first; Second second; /* process() calls both */ };
```

**Const by default.** Mark methods `const` when they don't change state,
parameters `const&` when they are large and only read, and locals `const`
when it helps a reader. (clang-tidy `misc-const-correctness`)

**Make wrong code fail to compile.** `enum class` instead of `enum`;
`explicit` single-argument constructors; `[[nodiscard]]` on functions whose
result must be used; `constexpr` for every compile-time constant;
`std::span` instead of pointer-plus-length; `std::array` instead of C arrays.
(clang-tidy `modernize-*`, `cppcoreguidelines-*`)

**`noexcept` on everything that cannot throw**, which includes all
audio-thread code. It documents the contract and helps the optimizer.

---

## 2. Naming and layout

Enforced by `.clang-format` and `readability-identifier-naming` in
`.clang-tidy`.

| Thing | Style | Example |
| --- | --- | --- |
| Classes, structs, enums, concepts, template parameters | `UpperCamelCase` | `DiodeClipper`, `SampleType` |
| Functions, variables, members, parameters, enum values | `lowerCamelCase` | `setCutoffHz()`, `sampleRate` |
| `constexpr` constants | `lowerCamelCase` | `rampSeconds` |
| Namespaces | `lowercase` | `pedallab` |
| Macros (avoid them) | `PEDALLAB_UPPER_CASE` | `PEDALLAB_NONBLOCKING` |

- No prefixes or suffixes on members (`m_`, `_`), no Hungarian notation.
- **Put units in names** whenever a value has one: `cutoffHz`, `gainDb`,
  `delayMs`, `timeSeconds`, `gainLinear`. Most DSP bugs that survive review
  are unit bugs (Hz vs radians, dB vs linear, ms vs samples).
- Template parameters get real names (`SampleType`, not `T`).
- Allman braces, 4 spaces, 120 columns, `Type* pointer`, `const` before the
  type. clang-format handles all of it; never hand-format.
- Floating literals have digits on both sides of the point and the right
  suffix: `0.5f`, `1.0`, never `.5` or `1.f`.
- Compare pointers explicitly: `if (ptr != nullptr)`, not `if (ptr)`.
  (clang-tidy `readability-implicit-bool-conversion`)

**File layout:** one class per header, file named after the class
(`DiodeClipper.h`). Class members in this order: public interface, then
private helpers, then data members last.

---

## 3. Real-time rules

The audio callback must finish within a deadline every time, not on average.
Anything that can take an unbounded amount of time is forbidden on the audio
thread: anything reachable from `processBlock()` or a `process*()` method.

**Forbidden on the audio thread**
- Memory allocation and deallocation, including hidden ones: growing a
  `std::vector`, `std::string`, constructing a `std::function` that captures,
  `juce::String`, `juce::Array` resizing, `std::shared_ptr` copies (atomic
  ref counting plus a possible free).
- Locks and waiting: `std::mutex`, `juce::CriticalSection`, condition
  variables, `sleep`, spinning on a flag without a bound.
- System calls and I/O: files, sockets, logging, `printf`, `DBG`,
  `std::cout`.
- Exceptions, and calls into anything that may throw.
- Unbounded algorithms: anything whose worst case is not known, including
  amortized-constant operations like `push_back`.

**Required**
- Allocate everything in the constructor or `prepare()`, sized for the
  maximum block size and sample rate the host promised.
- Mark audio-thread functions `noexcept` and `PEDALLAB_NONBLOCKING`. The
  realtime sanitizer preset (`rtsan`) then aborts on any violation.
- Wrap `processBlock()` in `juce::ScopedNoDenormals`. Denormal numbers
  (tiny values in decaying filters and reverb tails) can be 100x slower on x86.
- Keep the worst case close to the average case: avoid code paths that only
  run occasionally but are expensive (recomputing a big table when a
  parameter changes, for example). Compute such things off the audio thread
  and hand them over.

---

## 4. Sharing data between threads

The UI thread (knobs, editor) and the audio thread run concurrently.

| What crosses threads | Use |
| --- | --- |
| A single number (a parameter) | `std::atomic<float>` / `std::atomic<int>`. JUCE's `AudioProcessorValueTreeState::getRawParameterValue()` already gives you one. |
| A stream of events or messages | A single-producer, single-consumer lock-free FIFO (`juce::AbstractFifo` in plugin code). Exactly one writer thread and one reader thread. |
| A large object that changes occasionally (a lookup table, an impulse response) | Build it on a background thread, then swap a pointer atomically. Release the old one off the audio thread. Ask before implementing: this is easy to get subtly wrong. |

- Never share a non-atomic variable between threads without one of the
  above, even "just a bool". It is undefined behavior; the thread sanitizer
  preset (`tsan`) reports it.
- Use the default (sequentially consistent) memory order unless a comment
  explains why a weaker one is correct.
- Never call `AudioProcessorEditor` or other UI code from the audio thread.

---

## 5. DSP code conventions

**Processor shape** (see `pedallab::Gain`):

```cpp
class Processor
{
public:
    void prepare(double sampleRate) noexcept;   // off the audio thread; may compute tables
    void reset() noexcept;                       // clear state, snap smoothed values
    void setSomethingHz(float value) noexcept;   // cheap; safe between blocks
    PEDALLAB_NONBLOCKING void process(std::span<float> block) noexcept;
};
```

- `dsp/` has **no JUCE dependency**: standard library only, so it can be
  tested alone and reused on iOS, in WebAssembly, or with another framework.
- **State persists across blocks.** Filter memory, phase, flip-flop state and
  smoothed values are members, never locals reset at the top of `process()`.
  A block of 1 sample and a block of 4096 samples must produce identical
  output; tests check this.
- **Sample-rate independence.** Anything defined in seconds or hertz is
  converted to samples or coefficients in `prepare()`. Never hard-code 44100
  or 48000.
- **Smooth parameters** that change gain or filter coefficients, so automation
  doesn't produce zipper noise or clicks.
- **Precision:** `float` for audio samples and per-sample state in most
  processors; `double` for coefficient calculation, phase accumulators and
  filters with very low cutoffs. Convert with `static_cast`, never
  implicitly (`-Wconversion -Wdouble-promotion` enforce this).
- **Keep the inner loop simple:** no allocation, no virtual calls, no
  per-sample branching on parameters when it can be hoisted out of the loop.
  Optimize only with a benchmark showing the need.
- **Cite the math.** Each processor's header names its source: a paper, a
  book section, a schematic, or the Python experiment it ports. Equations go
  in a comment above the code that implements them.
- **Aliasing:** any nonlinearity (clipping, rectification, waveshaping) must
  state how it handles aliasing (oversampling factor, ADAA, or "none, known
  limitation") in its header comment.

---

## 6. Errors and assertions

- No exceptions on the audio thread. Elsewhere, only for genuinely
  exceptional failures (a missing file in a test, for example).
- Preconditions that indicate a programming error are assertions:
  `assert()` in `dsp/`, `jassert()` in plugin code. They compile out in
  release builds, so they must not have side effects.
- Never silently "fix" bad input on the audio thread with expensive checks.
  If NaN or inf could appear (feedback paths, unstable filters), handle it
  deliberately and test that case.

---

## 7. Tests

- Every processor has unit tests for its contract (unity gain at defaults,
  silence in gives silence out, reset clears state, block-size independence)
  and a reference test against its Python prototype.
- Reference tolerances are stated with a reason (`1e-6f` for identical math,
  looser where float vs double or a different filter discretization
  justifies it).
- A failing test is fixed or explained, never loosened or deleted to get a
  green build.
- Tests may allocate and throw; they are not real-time code.

---

## 8. Dependencies

- Standard library and JUCE first. New libraries need a reason and approval,
  and are pinned to exact versions in `cmake/Dependencies.cmake`.
- Libraries worth knowing before writing something by hand: chowdsp_utils
  (DSP building blocks, by Jatin Chowdhury), and JUCE's own `juce_dsp`
  module (in plugin code only, since `dsp/` stays JUCE-free).

---

## 9. Enforcement

| Check | Enforces | Where |
| --- | --- | --- |
| Compiler warnings as errors (`-Wall -Wextra -Wpedantic -Wconversion -Wshadow -Wold-style-cast` and more) | implicit conversions, shadowing, C casts | every build |
| `.clang-format` | all layout rules | CI `format` job |
| `.clang-tidy` (bugprone, cppcoreguidelines, modernize, performance, readability, naming) | ownership, const, naming, modern idioms | CI `linux` job |
| AddressSanitizer, UndefinedBehaviorSanitizer | memory errors, UB | CI `sanitizers` job |
| ThreadSanitizer | data races | CI `sanitizers` job |
| RealtimeSanitizer (`rtsan` preset, Clang 20+) | allocation, locks, syscalls in `PEDALLAB_NONBLOCKING` code | local, with Homebrew/LLVM Clang |
| Catch2 unit and reference tests | behavior, match with Python | every build |
| pluginval, strictness 10 | host-like stress (threads, buffer sizes, state) | CI |

---

## 10. Review checklist

Before a change is done, every item is true:

- [ ] Nothing reachable from `process*()` allocates, locks, does I/O or throws.
- [ ] Audio-thread functions are `noexcept` and `PEDALLAB_NONBLOCKING`.
- [ ] Data shared between threads is atomic or goes through a FIFO.
- [ ] State survives across blocks; results don't depend on block size.
- [ ] Nothing assumes a particular sample rate.
- [ ] Values with units have the unit in their name.
- [ ] The header cites the source of the math and states aliasing handling.
- [ ] Unit tests and a reference test cover the change.
- [ ] Builds clean with warnings as errors; clang-tidy and clang-format pass.
- [ ] `ctest` passes in `dev` and `asan`; `pytest` passes.
