Behaviour-preserving throughout: the acceptance is that every leaf's
world matrix is unchanged at every pose against the pre-cycle-2
reference, so evidence is captured before the edit and compared after.
Work from the project root with `PYTHONPATH=.` and the workspace venv
(`/home/asa/devel/libresolid-studio/.venv/bin/python`,
`.venv/bin/solid`). One heavy process at a time, in the foreground.

## 0. Pre-existing state

- [x] 0.1 `git rev-parse --show-toplevel` confirms this repository;
      `git status --porcelain` clean at `10873b5` on branch
      `version_4` before any edit.
- [x] 0.2 Baseline suites on the current framework (main, `63a2099`,
      ADR-098 already merged, this project not yet migrated):
      `PYTHONPATH=. .venv/bin/solid test --faceted simulation/hangprinter.py`
      — 19 tests, **14 passed, 5 failed** (the stack's stale
      parent-frame joints read wrong under ADR-097:
      `test_the_stacks_turn_by_the_line_they_pay_out`,
      `test_the_sense_pays_out`, `test_the_belt_travels_with_its_gear`,
      `test_the_teeth_ride_together`, `test_assembly_integrity`).
      `PYTHONPATH=. .venv/bin/solid test --faceted simulation/winch.py`
      — 5 tests, 5 passed, 0 failed (this suite never turns the stack).

## 1. `RotorABC.turn` / `RotorD.turn` — own-frame literals (ADR-097)

- [x] 1.1 `RotorABC.turn`: `axis=(0.0, 0.0, 1.0)`, `at` deleted (RESTATES
      the parent's own placement of the rotor).
- [x] 1.2 `RotorD.turn`: same rewrite, its own axis and anchor collapse
      to the identical literal.

## 2. `MotorGear.turn`, `RollerBearing.spin` — declared at the site (ADR-098)

- [x] 2.1 Added `MOTOR_SHAFT = tuple(float(v) for v in layout.MOTOR_SHAFT)`
      beside `BELT_ROLLER_AXIS`.
- [x] 2.2 Deleted `MotorGear.turn` and `RollerBearing.spin`'s class-body
      declarations; updated both classes' docstrings to say the joint
      is now declared at the site.
- [x] 2.3 `WinchABC.motor_gear` and `WinchD.motor_gear`: added
      `turn=Revolute(axis=SHAFT_AXIS, at=MOTOR_SHAFT, unit='deg')`
      (`WinchABC`'s keeping its own `mirrored=left_handed`).
- [x] 2.4 `WinchABC.rollers` and `WinchD.rollers`: added
      `spin=Revolute(axis=SHAFT_AXIS, at=BELT_ROLLER_AXIS, unit='deg')`
      to the `RollerBearing(...)` the `.repeat(2)` wraps — the ORIGINAL
      single-class repeat shape, no split into two named leaves.

## 3. The roller spin as a relation (ADR-096)

- [x] 3.1 `WinchABC` and `WinchD`: added
      `rotor.drives(rollers.spin, ratio=-SENSE * ROLLER_RATIO)` beside
      the two existing `rotor.drives(...)` relations.
- [x] 3.2 `WinchABC.simulate()` / `WinchD.simulate()`: deleted the
      per-roller hand loop; kept only
      `if self.rotor.turn.value is None: self.rotor.turn = 0.0` (the
      unrelated "a winch built on its own stands still" default,
      `move-onto-motion`'s own known gap 2).

## 4. Evidence again

- [x] 4.1 `PYTHONPATH=. .venv/bin/solid test --faceted simulation/hangprinter.py`
      — 19 tests, **19 passed, 0 failed**.
- [x] 4.2 `PYTHONPATH=. .venv/bin/solid test --faceted simulation/winch.py`
      — 5 tests, 5 passed, 0 failed (unchanged from baseline).
- [x] 4.3 Captured after-poses
      (`docs/motion-general-refactor/capture_poses.py capture
      simulation.hangprinter:Hangprinter <out.json>` — 11 poses, 149
      leaves) and compared against the pre-cycle-2 reference
      `before2/hangprinter-hangprinter-before.json`: **max deviation
      0.000e+00 over 11 poses**.
- [x] 4.4 Committed in this repository only, naming ADR-096, ADR-097,
      ADR-098 and the evidence rows. Not archived: the pilot/orchestrator
      reviews and archives.
