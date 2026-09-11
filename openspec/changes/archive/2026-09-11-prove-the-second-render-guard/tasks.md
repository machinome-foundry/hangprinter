# Tasks

Evidence-only: no source file changes. Run everything from the project
root with `PYTHONPATH=.` and the workspace venv. Never two heavy
processes at once. Never edit a test.

## 0. Pre-existing state

- [x] 0.1 `git rev-parse --show-toplevel` names this repository
      (`.../projects/3D-Printers/hangprinter`); `git status` was clean
      on branch `version_4` before this change touched anything.
- [x] 0.2 Confirm ADR-099 (`whole-tree-fixpoint`) is on solid-node main
      that the workspace venv imports — read `design.md` §6 and
      `evidence.md` §0.6.

## 1. Read the two sites named in the briefing

- [x] 1.1 `simulation/winch.py`, `WinchABC.simulate()` (line 335-337)
      and `WinchD.simulate()` (line 375-377): both already read
      `if self.rotor.turn.value is None: self.rotor.turn = 0.0` — the
      rebind is INSIDE the guard, the plain safe idiom. No unconditional
      rebind exists at either site. Grepped the whole `simulation/`
      package for `is None` (`simulation/winch.py` only, both lines
      above) and for any other unconditional-write-after-guard shape:
      none found.
- [x] 1.2 `simulation/hangprinter.py`, `Hangprinter.simulate()`: the
      ancestor binds `winch.rotor.turn` with NO guard at all, every
      render, whenever a winch is part of the assembled machine — the
      other correct shape, "no guard at all where an ancestor always
      binds it." The `WinchABC`/`WinchD` guard is exercised only when a
      winch is built standalone.

## 2. Evidence

- [x] 2.1 Run the two suites, one process at a time, in the foreground:

          PYTHONPATH=. .venv/bin/solid test --faceted simulation/hangprinter.py
          PYTHONPATH=. .venv/bin/solid test --faceted simulation/winch.py

      **Result:** `simulation/hangprinter.py` 19/19.
      `simulation/winch.py` 5/5. Unchanged (no source edit was made).
- [x] 2.2 Capture poses and compare against the true pre-campaign
      reference:

          PYTHONPATH=. .venv/bin/python \
              docs/motion-general-refactor/capture_poses.py capture \
              simulation.hangprinter:Hangprinter <captured.json>
          # captured 11 poses, 149 leaves
          .venv/bin/python docs/motion-general-refactor/capture_poses.py \
              compare before2/hangprinter-hangprinter-before.json <captured.json>
          # max deviation 0.000e+00 over 11 poses

      **Maximum deviation 0.000e+00.**
- [x] 2.3 Second-render probe on the assembled `Hangprinter` at
      `defaults` (`scratchpad/sr/second_render_probe.py`,
      `set_state(defaults)` → snapshot → `assemble()` → snapshot →
      `set_state(defaults)` → snapshot → `set_state(defaults)` →
      snapshot): **maximum deviation 0.000000 mm** across all three
      transitions. At `defaults` every winch's `rotor.turn` is
      genuinely `0.0`, so this result does not by itself distinguish a
      safe guard from a masked defect.
- [x] 2.4 The masking-breaking probe
      (`scratchpad/sr/winch_guard_nonzero_probe.py`, read-only,
      evidence-only, no project file touched): a standalone `WinchABC()`
      with `WinchABC.simulate` monkeypatched IN MEMORY to rebind
      `self.rotor.turn = 37.5` (keeping the guard's shape identical to
      the committed `0.0` case), enumerated three times
      (`set_state` → `assemble()` → `set_state`). `rotor.turn` reads
      `37.5` on every render; **maximum deviation between consecutive
      renders: 0.000000 mm.** This is the non-zero case ADR-099's own
      evidence named as needed to distinguish a safe guard from a
      masked one, and it comes back clean.

## 3. Commit

- [x] 3.1 Commit this OpenSpec change alone — no `simulation/` file
      changed — naming ADR-099 (`whole-tree-fixpoint`) and both the
      masked-at-defaults and masking-breaking evidence in the message.
      Do not archive.
- [x] 3.2 Report: the exact sentences read (both guard sites, the
      ancestor's unconditional bind), that no workaround was found or
      deleted, the second-render evidence at both the masked (defaults)
      and unmasked (37.5) cases, the pose comparison, suite counts, the
      commit.
