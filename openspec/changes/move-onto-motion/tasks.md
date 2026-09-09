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

- [ ] 2.1 `mover.py`: declare `travel_x`, `travel_y`, `travel_z` as
      `Prismatic` joints on `Mover`, axes `(1,0,0)`, `(0,1,0)`, `(0,0,1)`,
      no `at`, no `range`.
- [ ] 2.2 `hangprinter.py`: state `x.drives(mover.travel_x)`,
      `y.drives(mover.travel_y)`, `z.drives(mover.travel_z)` in the class
      body and delete `self.mover.translate([...])` from `simulate()`.
- [ ] 2.3 `winch.py`: declare `turn = Revolute(...)` on `RotorABC` and
      `RotorD` from `SANDWICH_ABC` / `SANDWICH_D` (axis = the placed +Z,
      anchor = the placed origin, both as tuples of plain floats);
      `turn = Revolute(axis=SHAFT_AXIS, at=tuple(MOTOR_SHAFT))` on
      `MotorGear`; `spin = Revolute(axis=SHAFT_AXIS, at=BELT_ROLLER_AXIS)`
      on `RollerBearing`. Add `SHAFT_AXIS`, `ROLLER_RATIO`,
      `BELT_MM_PER_DEGREE`, and per winch class `SENSE` and `BELT_SENSE`.
- [ ] 2.4 `winch.py`: state the two relations in each winch class —
      `rotor.drives(motor_gear.turn, ratio=SENSE * GEAR_RATIO)` and
      `rotor.drives(belt.travel, ratio=BELT_SENSE * BELT_MM_PER_DEGREE)`.
      Delete `_turn()`, the `line` port, `handed`, `GEAR_AXIS` and
      `ROLLER_AXES`; leave each winch a four-line `simulate()` that gives
      the stack a rest value when nothing bound it and fans the two
      rollers out at `-SENSE * ROLLER_RATIO`.
- [ ] 2.5 `ceiling.py`: delete the four `line_*` ports, the `lines`
      property and `simulate()`; promote `_sense` to
      `Ceiling.spool_sense(index)` using `self.sidelength` and the winch's
      `AXIS`. Keep the `winches` property.
- [ ] 2.6 `hangprinter.py`: bind each winch's stack coordinate by path in
      `simulate()` — `self.ceiling.winches[anchor].rotor.turn` — keeping
      today's arithmetic order exactly (sense on the millimetres, then
      `/ Spool_r`, then `* 180.0 / math.pi`). The strand loops,
      `_bind` and `_to_mover` stay.
- [ ] 2.7 Update the module docstrings that describe the old chain:
      `hangprinter.py` ("everything follows"), `ceiling.py` ("The ceiling
      reads four ports"), `winch.py` ("The winch reads one port, `line`").

## 3. Evidence again

- [ ] 3.1 Re-capture to `/tmp/hangprinter-after.json` and
      `capture_poses.py compare before after`: maximum world-matrix
      deviation 0 over every leaf and every pose. The port sets differ by
      construction — `line_a..d` and `winch.line` are gone, the joint
      coordinates (`turn`, `spin`, `travel_*`) are new — so report the
      matrix deviation and the port names added and removed separately.
- [ ] 3.2 Run both suites again: exactly the tests that were green at
      stage A are green, none newly red.
- [ ] 3.3 Commit as `refactor(simulation): move the Hangprinter onto
      solid-node joints and couplings`, with the pose result and the test
      counts in the body.
- [ ] 3.4 Report: the two commit hashes, the pose comparison line, test
      counts before and after, every deviation from the proposal (and why
      the nearest right thing was right), and every test you believe needs
      a change with the reason. Do not sync or archive this change; the
      orchestrator does that after review.
