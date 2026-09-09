Behaviour-preserving throughout: the acceptance is that every leaf's world
matrix is unchanged at every pose, so evidence is captured before the first
motion edit and compared after the last. Work from the project root with
`PYTHONPATH=.` and the workspace venv
(`/home/asa/devel/libresolid-studio/.venv/bin/python`, `.venv/bin/solid`).
Never run two suites at once. Never edit a test: if one blocks you, stop and
report the assertion.

## 0. Pre-existing state

- [x] 0.1 `git status --porcelain` is empty at `918d491` on branch
      `version_4`. Nothing to commit; if that has changed, commit the
      working state as its own commit first.
      Confirmed: tree was clean except the untracked
      `openspec/changes/move-onto-motion/` directory. No stage 0 commit
      needed.

## 1. Stage A — imports, baseline, poses

- [x] 1.1 Fix the three broken imports only: `TranslationalPort` in
      `simulation/part.py`, `simulation/ceiling.py` and
      `simulation/winch.py` now comes from `solid_node.motion.ports`.
      Nothing else changes. No test file imports a moved name.
- [x] 1.2 `PYTHONPATH=. .venv/bin/solid test --faceted simulation/hangprinter.py`
      — 19 tests, 19 passed, 0 failed (17 `HangprinterTest` +
      2 `HangprinterScenarioTest`, run together as one suite of 19).
- [x] 1.3 `PYTHONPATH=. .venv/bin/solid test --faceted simulation/winch.py`
      (node `WinchABC`, 5 tests) — 5 passed, 0 failed.
- [x] 1.4 Capture poses:
      `PYTHONPATH=. python <shop>/docs/motion-general-refactor/capture_poses.py capture simulation.hangprinter:Hangprinter /tmp/hangprinter-before.json /tmp/hangprinter-instructions.json`
      — 20 poses (the standard set plus the nine instruction targets,
      `Home`/`HomeX`/`HomeY`/`HomeZ`/`Center`/`Lift`/`AnchorA`/`AnchorB`/`AnchorC`),
      149 leaves. `WinchABC` has no ranged driver of its own (its only
      coordinate is the `line` port, bound from outside), so it is not a
      declared model and gets no separate capture.
- [x] 1.5 Commit as `refactor(simulation): import ports from
      solid_node.motion`, with the baseline in the message, together with
      this change's `proposal.md` and `tasks.md`.

## 2. Stage B — the motion refactor

- [x] 2.1 `mover.py`: declare `travel_x`, `travel_y`, `travel_z` as
      `Prismatic` joints on `Mover`, axes `(1,0,0)`, `(0,1,0)`, `(0,0,1)`,
      no `at`, no `range`.
- [x] 2.2 `hangprinter.py`: state `x.drives(mover.travel_x)`,
      `y.drives(mover.travel_y)`, `z.drives(mover.travel_z)` in the class
      body and delete `self.mover.translate([...])` from `simulate()`.
      Written just after `mover = Mover(...)` is declared (not right
      after the `x`/`y`/`z` drivers, where `mover` does not exist yet) —
      not a deviation from the proposal's mechanism, just where Python
      class-body execution order requires the statement to live.
- [x] 2.3 `winch.py`: declare `turn = Revolute(...)` on `RotorABC` and
      `RotorD` from `SANDWICH_ABC` / `SANDWICH_D` (axis = the placed +Z,
      anchor = the placed origin, both as tuples of plain floats);
      `turn = Revolute(axis=SHAFT_AXIS, at=tuple(MOTOR_SHAFT))` on
      `MotorGear`; `spin = Revolute(axis=SHAFT_AXIS, at=BELT_ROLLER_AXIS)`
      on `RollerBearing`. Added `SHAFT_AXIS`, `BELT_ROLLER_AXIS`,
      `ROLLER_RATIO`, `BELT_MM_PER_DEGREE`, and per winch class `SENSE`
      and `BELT_SENSE` — measured `SENSE`/`BELT_SENSE` = -1/-1 on
      `WinchABC`, +1/+1 on `WinchD`, exactly the proposal's prediction.
- [x] 2.4 `winch.py`: stated the two relations in each winch class —
      `rotor.drives(motor_gear.turn, ratio=SENSE * GEAR_RATIO)` and
      `rotor.drives(belt.travel, ratio=BELT_SENSE * BELT_MM_PER_DEGREE)`.
      Deleted `_turn()`, both `line` ports, `handed`, `GEAR_AXIS` and
      `ROLLER_AXES`; each winch keeps a four-line `simulate()` that gives
      the stack a rest value when nothing bound it and fans the two
      rollers out at `-SENSE * ROLLER_RATIO`. Deviation: the proposal's
      sketch reads bare `SENSE` inside `simulate()`; `SENSE` is a
      class-body constant, not a lexical name a method body can see
      unqualified in Python, so the method reads `self.SENSE` (module
      global `ROLLER_RATIO` is read bare, correctly). Same value, correct
      attribute access.
- [x] 2.5 `ceiling.py`: deleted the four `line_*` ports, the `lines`
      property and `simulate()`; the module-level `_sense` function's body
      is now `Ceiling.spool_sense(index)` (inlined rather than kept as a
      free function the method calls through — "promoted to a one-line
      method" read literally). Kept the `winches` property.
- [x] 2.6 `hangprinter.py`: binds each winch's stack coordinate by path in
      `simulate()` — `self.ceiling.winches[anchor].rotor.turn` — keeping
      today's arithmetic order exactly (sense on the millimetres, then
      `/ Spool_r`, then `* 180.0 / math.pi`). The strand loops, `_bind`
      and `_to_mover` are unchanged. `Spool_r` is now imported in
      `hangprinter.py` (used to live only in `winch.py`).
- [x] 2.7 Updated the module docstrings that described the old chain:
      `hangprinter.py`, `ceiling.py`, `winch.py`.

## 3. Evidence again

- [x] 3.1 Re-captured to `/tmp/hangprinter-after.json` and
      `capture_poses.py compare before after`: **max deviation 0.000e+00
      over 20 poses**, zero problems reported. Port sets differ by
      construction, checked separately by diffing declared ports between
      the two snapshots at the `defaults` pose:
      removed — `ceiling.line_a/b/c/d`, `ceiling.winch_{a,b,c,d}.line`
      (8 ports); added — `mover.travel_{x,y,z}` (3), each
      `winch_*.rotor.turn` (4), each `winch_*.motor_gear.turn` (4), each
      `winch_*.rollers[0,1].spin` (8) — 19 new joint coordinates. Exactly
      the sets the proposal names as going and arriving.
- [x] 3.2 Ran both suites again: `simulation/hangprinter.py` 19/19
      passed (same 19 as baseline: 17 `HangprinterTest` +
      2 `HangprinterScenarioTest`); `simulation/winch.py` (`WinchABC`)
      5/5 passed (same 5 as baseline) — including the standalone-winch
      case (known gap 2), which the `if turn is None: ... = 0.0` rest
      binding keeps green with no test edit. No test went red.
- [x] 3.3 Committed as `refactor(simulation): move the Hangprinter onto
      solid-node joints and couplings`, with the pose result and the test
      counts in the body.
- [x] 3.4 Reported to the orchestrator (see the implementer's final
      message): the two commit hashes, the pose comparison line, test
      counts before and after, every deviation from the proposal, and no
      test believed to need a change. Not synced or archived here; the
      orchestrator does that after review.
