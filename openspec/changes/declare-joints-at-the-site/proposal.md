## Why

`move-onto-motion` (archived) put the Hangprinter's motion on
`solid_node.motion`'s joints and relations, in the frame reading that
existed at the time: a class-body joint's `axis`/`at` read in the
**parent's** frame, carried into the body's own frame by inverting the
rest placement. Two framework cycles have since changed that reading,
and this project's own joints have not caught up:

- **ADR-097** ("a joint is stated in the frame of whoever declares it")
  makes a class-body joint's `axis`/`at` read in the body's **own** rest
  frame instead. `RotorABC.turn` and `RotorD.turn` still carry the OLD
  parent-frame numbers (`_axis(SANDWICH_ABC)`/`SANDWICH_ABC[:3, 3]` and
  the `SANDWICH_D` equivalents) — read under the new rule they are
  **wrong**: on the current framework, before this change,
  `simulation/hangprinter.py`'s own suite is 14/19, the five reds all
  the stack failing to turn by the line it pays out
  (`test_the_stacks_turn_by_the_line_they_pay_out`,
  `test_the_sense_pays_out`, `test_the_belt_travels_with_its_gear`,
  `test_the_teeth_ride_together`, `test_assembly_integrity`).
- **ADR-098** ("a joint may be declared where a child is placed") gives
  a class placed at several sites with a shared axis and opposed
  attitudes — `MotorGear`, placed unmirrored and mirrored, and
  `RollerBearing`, `.repeat(2)`'d Rx(+90)/Rx(−90) — a way to state that
  axis once, at each site, in the **parent's** frame, rather than
  needing a callable of the realized node or abandoning the repeat. Both
  are named in `evidence/sightings.md` §4 (rows 3 and 4) and
  `evidence/survey.md:240-241` of the two framework cycles' own OpenSpec
  changes.
- **ADR-096** ("a relation broadcasts over a repeated child") lets a
  `drives` relation's driven end pass through `rollers`, the belt
  roller `.repeat(2)`: `WinchABC.simulate()` and `WinchD.simulate()`
  each carry a hand-written loop
  (`for roller in self.rollers: roller.spin = -self.SENSE *
  ROLLER_RATIO * turn`) whose own comment says why —
  *"a relation cannot yet fan out over a `.repeat()` child"* — a gap
  `move-onto-motion`'s own proposal recorded by name (its "Known gaps"
  §1) and the framework has since closed.

This change is this project's stage B on all three ADRs, per the shop's
motion-catalogue-refactor campaign
(`libresolid-studio/docs/motion-general-refactor.md`).

## What changes

### `RotorABC.turn` / `RotorD.turn`: own-frame literals (ADR-097)

Both anchors RESTATE the parent's own placement of the rotor
(`SANDWICH_ABC[:3, 3]` / `SANDWICH_D[:3, 3]`, exactly what `render()`
passes to `place()`) — under the own-frame default that placement is
already carried, so `at` is deleted outright. Both axes are the SAME
rotation's own transform of local `+Z`, carried back through the
inverse of that one rotation: `(0, 0, 1)` for both, replacing
`_axis(SANDWICH_ABC)` (`(0, -1, 0)`) and `_axis(SANDWICH_D)`
(`(0, 1, 0)`):

    turn = Revolute(axis=(0.0, 0.0, 1.0), unit='deg')

on both classes. Each has exactly one instantiation site
(`rotor = RotorABC()` in `WinchABC`, `rotor = RotorD()` in `WinchD`), so
this is a single-site recompute, not a declaration-site joint.

### `MotorGear.turn`, `RollerBearing.spin`: declared at the site (ADR-098)

Both classes are placed at two sites sharing one axis with opposed
attitudes — `MotorGear` unmirrored (`WinchD`, and `WinchABC` when
`left_handed` is false) and mirrored (`WinchABC` when `left_handed` is
true); `RollerBearing`'s `.repeat(2)` copies at `Rx(+90)`/`Rx(−90)` — so
neither axis is stateable as one own-frame literal on the class. Both
class-body joints are deleted and restated as a keyword where each
winch places its own child, in the PARENT's frame, exactly the
pre-cycle-2 parent-frame values (`SHAFT_AXIS`, the winch frame's own Y)
this project already had a name for:

    # WinchABC and WinchD, each `motor_gear` declaration
    motor_gear = MotorGear(mirrored=..., turn=Revolute(axis=SHAFT_AXIS, at=MOTOR_SHAFT, unit='deg'))

    # WinchABC and WinchD, each `rollers` declaration
    rollers = RollerBearing(spin=Revolute(axis=SHAFT_AXIS, at=BELT_ROLLER_AXIS, unit='deg')).repeat(2)

`MOTOR_SHAFT` is added beside the existing `BELT_ROLLER_AXIS`:
`layout.MOTOR_SHAFT` read back as plain floats, the same conversion the
deleted class-body declaration made. One site declaration on the
`rollers` repeat serves both copies through their own carry — the
module's own design decision (`SHAFT_AXIS`'s docstring, `winch.py:57-64`)
that "one declaration serves both the unmirrored and the mirrored
leaf" is unchanged in substance and now written at the site instead of
in the class body. Text is written twice for `motor_gear` (once per
winch class, `WinchABC`'s carrying `mirrored=left_handed`, `WinchD`'s
not) and once for `rollers` (each winch's `.repeat(2)` carries its own
copies through their own carry, so the repeat needs one declaration per
winch class, not one per copy).

### The roller spin: a relation, not a hand loop (ADR-096)

`WinchABC` and `WinchD` each gain one relation, beside their existing
two:

    rotor.drives(rollers.spin, ratio=-SENSE * ROLLER_RATIO)

`rollers` is the `.repeat(2)` child; the driven end is a broadcast,
resolving to one relation record per copy, both sharing the SAME
`ratio` (`ratio` resolves once against the declaring instance, per
ADR-096) — the differing physical sense between the two rollers comes
entirely from each copy's own carry of the shared `SHAFT_AXIS`, not
from the ratio. `WinchABC.simulate()` and `WinchD.simulate()` lose
their per-roller loop; what is left is only what a relation cannot
reach — the stack's own rest value when nothing drives it:

    def simulate(self):
        if self.rotor.turn.value is None:    # a winch built on its own stands still
            self.rotor.turn = 0.0

(`move-onto-motion`'s own "Known gaps" §2, unrelated to this change and
kept unedited.)

## What does not change

- `simulation/mover.py`'s three `Prismatic` joints (`travel_x/y/z`):
  `Hangprinter.render()` never places `self.mover`, so the declaring
  body's own rest frame already IS the parent frame — OWN-ORIGIN-ALREADY,
  no rewrite.
- Every relation already stated (`rotor.drives(motor_gear.turn, ...)`,
  `rotor.drives(belt.travel, ...)`, the three root `x`/`y`/`z` bindings),
  every `render()` placement, every layout matrix, every leaf class,
  every STL and `.scad` module, the line-length law in
  `Hangprinter.simulate()`.
- Every pose: this is a restatement under the current framework, proven
  by a before/after comparison against the SAME pre-cycle-2 reference
  poses `move-onto-motion` itself measured against.
- The design record (`openspec/specs/spool-drive`, `line-kinematics`,
  `line-path`, `mover-assembly`, `ceiling-unit-layout`,
  `anchor-station`): no behaviour changes, so this change carries no
  spec delta.

## Evidence

- Suite before this change, on the current framework (main,
  `63a2099`): `simulation/hangprinter.py` 14/19 (5 red, all the stack
  failing to turn correctly under the stale parent-frame joints);
  `simulation/winch.py` 5/5.
- Suite after: `simulation/hangprinter.py` 19/19; `simulation/winch.py`
  5/5 — the same five tests the pre-cycle baseline passed, unchanged.
- Poses: `docs/motion-general-refactor/capture_poses.py compare` against
  `before2/hangprinter-hangprinter-before.json` (the true, pre-cycle-2
  poses) — **max deviation 0.000e+00 over 11 poses, 149 leaves**.

## Deviation from the campaign's mechanical guides

The campaign's own read-only overlays
(`patch_hangprinter.py`, `site_patch_hangprinter.py`) proposed a
callable-of-`mirrored` for `MotorGear.turn`
(`axis=lambda node: (0.0, 0.0, -1.0 if node.mirrored else 1.0)`) as
cycle 2's own answer, before cycle 3 existed to do better. Per this
project's briefing this change uses the site form for `MotorGear`
too, matching `RollerBearing`: no callable, one anchor and one axis
literal at each site, the sign supplied entirely by each site's own
carry. No other deviation from the guides.
