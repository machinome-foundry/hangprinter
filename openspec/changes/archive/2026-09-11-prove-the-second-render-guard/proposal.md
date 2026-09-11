# Prove the second-render guard, no workaround found to delete

## Why

solid-node main integrated `whole-tree-fixpoint` (ADR-099) since this
project's own `move-onto-motion` + `declare-joints-at-the-site` stage B
(`89069b7`, archived `2026-09-10-declare-joints-at-the-site`). Among
ADR-099's decisions (design.md §6, "The stale author-bound joint"): at
the start of an assembly's simulate phase, the framework now CLEARS the
value and binder of every coordinate that assembly bound during its OWN
previous simulate phase — the author's own bindings included — so the
plain rest-default idiom the catalogue already writes,

    if coord.value is None:
        coord = default

now works correctly across repeated renders without any further help
from the project.

This is this project's stage B on ADR-099, alongside the same cycle's
Prusa i3 change (`clear-the-second-render-workaround`). Prusa's three
sites carried a defensive unconditional rebind outside the `is None`
guard — the workaround the framework gap made necessary before ADR-099 —
and that workaround is deleted there. **Reading this project's two
sites finds no such workaround to delete:**

    # simulation/winch.py, WinchABC.simulate() and WinchD.simulate()
    def simulate(self):
        if self.rotor.turn.value is None:    # a winch built on its own stands still
            self.rotor.turn = 0.0

The rebind (`self.rotor.turn = 0.0`) is already INSIDE the guard — the
plain, safe idiom ADR-099's own design document names as what the
catalogue already writes and what needed no rescue. `whole-tree-fixpoint`'s
own evidence (§0.6) found the same thing reading this exact code: "DO
bind inside the guard... the stale-value defect is present but has no
visible effect" — because the rest default here is exactly `0.0`, and a
stale (uncleared) value from a previous render would ALSO read `0.0`,
so a rest-default rebind and a no-op leave the winch in the identical
pose either way. The defect this guard's shape is vulnerable to was
never observable in this project's own normal operation; it was masked,
not fixed, by the value happening to be zero.

Separately, `Hangprinter.simulate()` — the ancestor — binds every
winch's `rotor.turn` UNCONDITIONALLY, with no guard at all, every single
render, whenever a `WinchABC`/`WinchD` is part of the assembled machine
(`winch.rotor.turn = radians * 180.0 / math.pi`, no `if` at all). This
is the OTHER shape ADR-099 stage B names as already correct — "no guard
at all where an ancestor always binds it" — and it means the
`WinchABC`/`WinchD` guard is a rest default for STANDALONE use only
(building a bare `WinchABC()`/`WinchD()`, as `simulation/test_winch.py`
does); inside the real machine, the ancestor's own relation overwrites
it every phase and the guard's branch never runs at all.

## What changes

Nothing in `simulation/`. Both sites already carry the correct shape;
there is no workaround to write, delete, or move. This change is
evidence-only: it proves the guard's shape is safe under ADR-099 even
where the project's own zero default cannot show it, and records the
regression check the campaign's evidence anticipated (`whole-tree-fixpoint`
evidence.md, "task 9.2 ... is already met at the base and stays met at
head — a regression check, not a fix-to-see demonstration, for these
two specific projects as currently committed").

## What does not change

- No printed body's geometry, mesh, or `.scad` source.
- No driver, instruction, relation, ratio, offset, or law.
- No test is edited. `test_hangprinter.py` (19 tests) and
  `test_winch.py` (5 tests) are read-only evidence; both pass in full,
  unchanged from the pre-cycle baseline.
- Every leaf's world matrix and every bound port at every captured pose.

## Evidence

- `solid test --faceted`, one suite at a time, workspace venv,
  `PYTHONPATH=.`: `simulation/hangprinter.py` 19/19,
  `simulation/winch.py` 5/5 — unchanged (no source edit was made).
- Pose comparison, `docs/motion-general-refactor/capture_poses.py`,
  11 poses / 149 leaves, against the true pre-campaign reference
  `before2/hangprinter-hangprinter-before.json`: **maximum deviation
  0.000e+00.** (No source edit means this project's own before/after
  states are the same file; the comparison is a regression check
  against the pre-cycle reference, not a before/after-this-edit diff.)
- Second-render probe on the assembled `Hangprinter` at its `defaults`
  pose (`set_state(defaults)` → snapshot → `assemble()` → snapshot →
  `set_state(defaults)` → snapshot → `set_state(defaults)` → snapshot,
  comparing each consecutive pair): **maximum deviation 0.000000 mm**
  across all three render transitions. At this pose every driver is 0,
  so every winch's `rotor.turn` is genuinely 0.0 both times — this
  result is consistent with the guard being safe AND with the defect
  being masked, and does not by itself distinguish the two.
- **The masking-breaking probe.** A read-only, evidence-only script
  (`scratchpad/sr/winch_guard_nonzero_probe.py`, no project file
  touched) builds a standalone `WinchABC()` — no ancestor ever binds
  `rotor.turn`, exactly as `test_winch.py` builds it — and monkeypatches
  ONLY the numeric literal in `WinchABC.simulate()`, in memory, for the
  duration of the run: `self.rotor.turn = 37.5` (Prusa's own historical
  second-render figure) in place of the committed `0.0`, keeping the
  guard's shape byte-for-byte otherwise identical. Enumerated three
  times (`set_state` → `assemble()` → `set_state`), `rotor.turn` reads
  `37.5` every time and **the maximum deviation between every
  consecutive pair of renders is 0.000000 mm.** This is the
  masking-breaking case ADR-099's own evidence named as needed
  ("hangprinter's zero-defaulted winches are covered by a test with a
  non-zero default") and confirms the framework's clear (not a
  project-side workaround) is what makes this exact guard shape safe.
