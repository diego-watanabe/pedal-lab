# pedal-lab: project context

Background and current status for picking up this project in a new
conversation. Update the status section as things change.

## Who and why

- CS major, EE minor (graduated 2013): did DSP math, controls, an audio
  engineering class, built a RAT-style distortion pedal and a textbook
  synthesizer in VHDL. Since then: web apps, ETL, mobile apps (including
  early Android and iOS SDKs; worked on the iHeartRadio app's streaming side).
- C++ last written in 2018 (Objective-C++); recent Rust. Knows OOP well,
  less familiar with modern C++ idioms.
- Goal: learn to build audio software (effects, synths, plugins, sound
  engines) by modeling pedals I own, software first, hardware later.
  Not for sale. Maybe an original OC-2-style design someday.

## Gear

- Interface: RME Babyface.
- Basses: active and passive StingRay (humbuckers), P-bass and Mustang
  (split coils), fretless Big Al (silent single coils).
- Pedals to model first: a ProCo RAT (clone built in college; real circuit
  not remembered) and a 3Leaf Audio Octabvre (OC-2 inspired octave down).
- Usual chain includes an Aguilar Tonehammer (bypassed for captures).
- Computer: Windows PC (desktop-ahpqqd1), repo at `Documents\pedal-lab`.

## How we work

- I write the Python prototypes and their tests (that's where I learn the
  DSP). AI writes most of the C++, held to `docs/CPP_STANDARDS.md` and
  checked against the Python by reference tests.
- C++ with JUCE (chosen over Rust/nih-plug for AU/AUv3/iOS support and
  ecosystem maturity).
- Explanations: assume the EE/DSP background, explain modern C++ and
  real-time audio practice.

## Repo map

See `README.md` and `docs/CODE_TOUR.md`. In short: `python/` (lab:
`run.py`, `live.py`, experiments, tests), `dsp/` (JUCE-free C++ library),
`plugins/` (JUCE wrappers, LabGain template), `tests/cpp/` (Catch2 +
reference tests), `docs/`, `scripts/` (Windows setup).

## Status (2026-10-17)

- Done: repo scaffold, Python lab with 8 exercises (01 gain complete),
  live mode, DC blocker worked example through the whole pipeline,
  C++ standards, development guide, code tour, Windows setup script.
  Everything builds and passes on Linux.
- Git: `Documents\pedal-lab` is a git checkout of `main`, pushed to
  https://github.com/diego-watanabe/pedal-lab (private). CI
  (`.github/workflows/ci.yml`) runs on every push to `main`. First run:
  python, format, linux (incl. pluginval) and the Linux sanitizers pass;
  the `windows` job fails at "Test with AddressSanitizer" (build and
  plain tests pass) and the `macos` job fails at "Build". Not yet
  diagnosed.
  `pedal-lab.bundle` is gone; GitHub is the history from now on.
- In progress: running `scripts\setup-windows.ps1`. Git and Visual Studio
  are installed. The conda step failed with an SSL error (old Anaconda);
  the fix is now in the folder (commit 8c1b9ce) but not yet confirmed by
  a rerun. The script's git step will report "already set up".
- Not done: RME ASIO driver, first Windows C++ build, first push from
  Windows (Git Credential Manager will ask to sign in to GitHub).
- Next milestone: a passthrough (`python/experiments/00_passthrough.py`,
  `y = x`) played live with the bass, then exercises 02 to 08, then
  captures of the Octabvre and RAT.
