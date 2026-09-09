## Why

solid-node's motion layer (`solid_node.motion.{ports,joints,couplings}`)
moved `Port`, `TranslationalPort` and `Time` out of `solid_node.node` with
no re-export, so this simulation no longer imports:

    ImportError: module 'solid_node.node' has no attribute
    'TranslationalPort': ports and the declared time base moved to
    'solid_node.motion.ports'.

Fixing the three imports (`part.py`, `ceiling.py`, `winch.py`) would make
the model run again, but the machine would still be stated the way it was
stated before joints and relations existed: a chain of forwarding ports
(root -> `ceiling.line_a` -> `winch.line`), three `simulate()` methods that
hand-turn bodies with `rotate(...)`, and a page of sign arithmetic
(`handed`, `_sign(GEAR_AXIS, rotor_axis)`, `_sign(axis, rotor_axis)`,
`_axis(MOTOR_GEAR)`) whose only job is to work out which way a part's own
frame points relative to the frame the winch is drawn in.

The Hangprinter is a cable robot, so what it does is short to say and the
model should say it in that many words:

- the **mover** hangs free in the machine frame and is placed at `(x, y,
  z)` — three translational freedoms against the ceiling, one per driver,
  and no rotation: the layout gives it none and the simulation gives it
  none;
- the **four winches** each have one freedom — the spool stack turning at
  its bearing — driven by the line that winch pays out, which is a
  prescribed non-affine law of the mover's position (`|anchor - pos|`),
  not something one coordinate does to another;
- everything below the stack **is** a transmission: the motor gear at
  `255/20`, the belt at the spool gear's pitch-line travel, the two belt
  roller bearings at the belt's speed over their 5 mm rim.

The first two become joints, the third becomes `drives` sentences with a
ratio, and every forwarding port and every frame-sign constant in the
motion path goes away. Poses do not change: this is a restatement, and
the acceptance is that every leaf's world matrix is identical at every
pose.

## What changes

### The mover: three prismatic joints (`simulation/mover.py`)

`Mover` declares its three freedoms against the ceiling, on the body that
has them:

    travel_x = Prismatic(axis=(1, 0, 0), unit='mm')
    travel_y = Prismatic(axis=(0, 1, 0), unit='mm')
    travel_z = Prismatic(axis=(0, 0, 1), unit='mm')

Numbers: none. The mover has no rest placement at all — `Hangprinter.
render()` never places it — so the parent frame is the machine frame and
the axes are the machine's own, exactly the frame `Hangprinter.simulate()`
translates in today (`self.mover.translate([self.x, self.y, self.z])`).
`at` is left at the origin (a `Prismatic`'s anchor never affects its
placement). **No `range` is declared**: the drivers already carry
`(-REACH, REACH)` and `(0, Z_MAX)` as the sliders' presentation, a joint
range would newly refuse a numeric binding outside it, and nothing in the
machine needs that refusal.

Three joints on one body is more than one freedom on one body, which the
campaign's other projects have been deferred for. It is safe here and
only here: three **orthogonal translations commute**, so
`T(x)·T(y)·T(z)` is the same body placement in whatever order the
framework composes them, and the joints spec's composition-in-binding-order
cannot change the pose. The published operations become three translations
(`[x,0,0]`, `[0,y,0]`, `[0,0,z]`, with plain numeric zeros per the spec)
where there was one; their product is bit-identical to today's single
`translate([x, y, z])`.

### The mover's drivers: three relations (`simulation/hangprinter.py`)

In the `Hangprinter` class body, naming the coordinate at both ends:

    x.drives(mover.travel_x)
    y.drives(mover.travel_y)
    z.drives(mover.travel_z)

Ratio 1, offset 0 — the driver is in millimetres of the machine frame and
so is the joint. `self.mover.translate([...])` leaves `simulate()`.

### The winch stacks: one revolute each (`simulation/winch.py`)

`RotorABC` and `RotorD` each get the one freedom their winch has:

    # RotorABC
    turn = Revolute(axis=tuple(_axis(SANDWICH_ABC)),
                    at=tuple(SANDWICH_ABC[:3, 3]), unit='deg')
    # RotorD
    turn = Revolute(axis=tuple(_axis(SANDWICH_D)),
                    at=tuple(SANDWICH_D[:3, 3]), unit='deg')

Numbers: read off the layout matrix that places the rotor in the winch
frame — `SANDWICH_ABC` and `SANDWICH_D` — the same matrix `render()`
passes to `place()`, so the declared axis is the rotor's own placed +Z
(`(0, -1, 0)` for A/B/C, `(0, 1, 0)` for D) and the anchor is its own
placed origin. The framework carries both back into the rotor's frame and
finds the local axis `(0, 0, 1)` through the local origin, so what is
applied is one rotation and nothing else — literally today's
`winch.rotor.rotate(degrees, [0, 0, 1])`. `axis` and `at` are written as
tuples of plain floats (`tuple(float(v) for v in ...)`), computed once at
import as today's `AXIS` is. No `range`: the spool turns as many
revolutions as the machine asks for.

Keep `WinchABC.AXIS` / `WinchD.AXIS` as the class constant they are today
(`test_hangprinter.winch_axes` and `Ceiling` read the stack axis), and let
the joint declaration use the same expression.

### The motor gear and the belt rollers: one revolute each, on the leaf

    # MotorGear
    turn = Revolute(axis=SHAFT_AXIS, at=tuple(MOTOR_SHAFT), unit='deg')

    # RollerBearing
    spin = Revolute(axis=SHAFT_AXIS,
                    at=(Belt_roller_bearing_xpos, 0.0,
                        belt_roller_bearing_center_z), unit='deg')

with `SHAFT_AXIS = (0.0, 1.0, 0.0)`, the winch frame's Y — the direction
every one of these bodies turns about in every winch, and the one
`test_winch.py` already writes down as `MOTOR_AXIS` and `ROLLER_AXIS`.

Numbers and why they are one declaration for four winches and for both
rollers:

- `MOTOR_SHAFT` is already exported by `layout.py` as "the motor shaft's
  axis in the winch frame: along Y, through this point". The mirrored
  placement `MOTOR_GEAR_MIRRORED` differs from `MOTOR_GEAR` only by
  `M([1, 0, 0])` in the bracket frame, whose displacement is `±_GEAR_X`
  **along the shaft**, so mirrored and unmirrored gears sit on one line
  and one `at` serves both. No callable of the realized node is needed,
  and `MotorGear.mirrored` stops meaning anything to the motion.
- `BELT_ROLLERS` places its two bearings with `R([90,0,0])` and
  `R([-90,0,0])` and then `T([0, 0, -b623_width - 0.1])`, i.e. offset from
  `(Belt_roller_bearing_xpos, 0, belt_roller_bearing_center_z)` **along
  Y** in opposite directions: two bearings on one stud, one axis line, so
  one anchor serves both copies. That point is `BELT_ROLLER_CENTRE` read
  back into three dimensions.

Declaring the axis in the *winch's* frame rather than each leaf's own +Z
is what deletes the sign arithmetic: the framework carries `(0, 1, 0)`
into each body's own frame (finding `(0, 0, ±1)` there according to how
the layout drew it, mirrored gears included) and the ratios below are then
plain mechanism numbers.

### What drives what, in the winch class bodies

`GEAR_RATIO = GT2_spool_gear_teeth / GT2_motor_gear_teeth` (255/20)
already exists. Add, beside it:

    ROLLER_RATIO = SPOOL_PITCH_RADIUS / ROLLER_RADIUS
    BELT_MM_PER_DEGREE = SPOOL_PITCH_RADIUS * math.pi / 180.0

and in each winch class, one constant that says which way its stack axis
points against the shared shaft axis, derived from the layout exactly as
today's senses are, evaluated once at class definition:

    SENSE = _sign(SHAFT_AXIS, AXIS)          # -1 on A/B/C, +1 on D
    BELT_SENSE = -_sign(AXIS, WRAP_NORMAL)   # -1 on A/B/C, +1 on D

Then, in `WinchABC` and in `WinchD` (same two sentences, each class's own
constants):

    rotor.drives(motor_gear.turn, ratio=SENSE * GEAR_RATIO)
    rotor.drives(belt.travel, ratio=BELT_SENSE * BELT_MM_PER_DEGREE)

Both ends named: `rotor` stands for `RotorABC.turn` (its class's one
joint), the driven ends are `MotorGear.turn` (degrees about the shaft
axis) and `Belt.travel` (millimetres of belt, the molejo phase).

Where the numbers come from, and that they are today's:

- **Motor gear.** Both pulleys are inside the toothed loop, so the gear
  turns the stack's way at the tooth ratio. Today's model writes the same
  rotation as `handed * _sign(GEAR_AXIS, rotor_axis) * GEAR_RATIO *
  degrees` about the gear's own +Z; with both coordinates measured about
  the winch frame the rotation vector is `+GEAR_RATIO · θ_rotor · AXIS`,
  whose component about `SHAFT_AXIS` is `SENSE * GEAR_RATIO * θ_rotor`.
  `handed`, `GEAR_AXIS` and the "a leaf drawn mirrored turns the other
  way" comment all go.
- **Belt.** `SPOOL_PITCH_RADIUS` is the spool gear's pitch radius
  (`belt_circles()[0]['radius']`), so a degree of stack turn is
  `π/180 · SPOOL_PITCH_RADIUS` millimetres of belt. `BELT_SENSE` is
  today's `-_sign(rotor_axis, WRAP_NORMAL)`: molejo circulates the tooth
  pattern against the loop's clockwise run for a positive phase, so the
  sense is a fact about the wrap's normal, not about the machine. It stays
  as one derived constant per class, with today's comment.
- **Rollers** — see "Known gaps": the ratio is
  `-SENSE * ROLLER_RATIO`, the belt's back on the bearing turning it the
  gears' opposite way, but it cannot be written as a `drives` sentence.

### The line each winch pays out: bound by path from the root

The root already owns the only thing that is not a transmission — the
mover's position — and it already computes the anchor distances
symbolically. It now binds the stack coordinate directly, two levels
down, instead of pushing millimetres through two ports:

    for anchor in (A, B, C, D):
        winch = self.ceiling.winches[anchor]
        rest = layout.line_length(anchor, (0.0, 0.0, 0.0))
        paid = ADVANTAGE[anchor] * (self.line_length(anchor) - rest)
        radians = self.ceiling.spool_sense(anchor) * paid / Spool_r
        winch.rotor.turn = radians * 180.0 / math.pi

The arithmetic is today's, in today's order and association (sense applied
to millimetres, then `/ Spool_r`, then `* 180.0 / math.pi`), so the
published angle expression is bit-identical.

`Ceiling.spool_sense(index)` is today's module function `_sense(index,
winch.AXIS, sidelength)` promoted to a one-line method, because which way
a winch's line leaves its spool is the ceiling's knowledge (its docstring
says so) and it needs `self.sidelength` and its winch's axis. It is a
method, not a port: nothing forwards a value through it.

### Ports that go, ports that stay

**Go** (their only job is carrying a value one level down):

- `Ceiling.line_a`, `line_b`, `line_c`, `line_d` and the `lines`
  property — no test reads them;
- `WinchABC.line`, `WinchD.line`.

**Stay**, because they feed molejo geometry rather than a body's
placement — the chain is driver -> port -> shape:

- `Strand.x`, `Strand.y`, `Strand.z` (34 strands): `Line(to=[P.x, P.y,
  P.z])`. Their 34 bindings stay in `Hangprinter.simulate()`; a line's end
  point is not a freedom of a body and the strands are `.repeat()`
  children anyway.
- `Belt.travel`: `Wrap(phase=P.travel)`. It stays a `TranslationalPort`
  and is now the driven end of a relation instead of a `connect()` call.

### `simulate()` methods

- `Ceiling.simulate()` — **deleted** (five lines, the `_sense` call per
  winch per instant included; the sense is now computed once per
  binding by `spool_sense`, and per realization is not worth a change).
- `WinchABC.simulate()` / `WinchD.simulate()` and the module-level
  `_turn()` (14 lines) — replaced by four lines that bind only what a
  relation cannot reach:

        def simulate(self):
            turn = self.rotor.turn.value
            if turn is None:            # a winch built on its own stands still
                self.rotor.turn = turn = 0.0
            for roller in self.rollers:
                roller.spin = -SENSE * ROLLER_RATIO * turn

- `Hangprinter.simulate()` — loses the mover placement (three relations)
  and the four-port loop becomes the four-joint binding above; the strand
  loops and `_bind`/`_to_mover` stay unchanged.
- `Mover.simulate()`, `Anchor.simulate()` — do not exist and are not
  added.

### Frame arithmetic that leaves

`handed` (the mirrored-gear sign), `GEAR_AXIS`, `ROLLER_AXES`, `_axis`
applied to `MOTOR_GEAR`/`BELT_ROLLERS`, the per-roller
`_sign(axis, rotor_axis)`, and the per-instant `_sign(GEAR_AXIS,
rotor_axis)`. `_axis`, `_sign` and `WRAP_NORMAL` survive to compute two
constants per winch class (`AXIS`, `SENSE`, `BELT_SENSE`) and the two
rotor joint declarations, all at import.

### Counts

7 joint declarations (3 prismatic on the mover, 1 revolute on each of
`RotorABC` and `RotorD`, 1 on `MotorGear`, 1 on `RollerBearing`) covering
19 moving coordinates; 7 relations (3 at the root, 2 in each winch class);
0 derived coordinates — nothing here is a linear formula over two
coordinates; 4 hand bindings of a stack coordinate (the prescribed law
below) and 8 hand bindings of a roller (the gap below).

## What does not change

- The drivers `x`, `y`, `z`, their units, defaults and ranges; the nine
  instructions and their targets and durations.
- Every placement in `render()`, in `layout.py`, and every matrix in it;
  every leaf class, every STL and every `.scad` module read.
- The design record: `openspec/specs/line-kinematics`, `spool-drive`,
  `line-path`, `mover-assembly`, `ceiling-unit-layout`, `anchor-station`
  describe behaviour, and no behaviour changes, so this change carries no
  spec delta.
- Every test file and every assertion (see "Tests").
- `Ceiling.winches`, `WinchABC.AXIS`, `WinchD.AXIS` — read by the tests.
- `csg.py`, `measure.py`, `frames.py`, `gt2.py`, `materials.py`,
  `scad.py`, `anchor.py` (`anchor.py` gets no joint: an anchor stands
  still).
- The mover's pose at every driver value, every strand's two ends, every
  spool angle, every belt phase.

## Known gaps

1. **A relation cannot fan out over a `.repeat()` child** (recorded in
   `solid-node/workflow/warts.md`, "Motion catalogue refactor"). Each
   winch's two belt roller bearings are `rollers = RollerBearing().repeat(2)`
   and the couplings spec refuses a path through a repeated declaration.
   The sentence the project wants is:

       rotor.drives(rollers.spin, ratio=-SENSE * ROLLER_RATIO)

   one relation per winch class, no `simulate()` at all in `winch.py`.
   Until then the eight bearings are bound in a two-line loop — a joint
   binding now, not a `rotate()`, so a later primitive *adds* to this
   rather than redoing it. This is dressing (a bearing spinning under the
   belt), not the machine's principal motion, so it does not defer the
   project.

2. **Both ends of a relation unbound is refused, and `test_winch.py`
   builds a winch on its own.** `WinchABC` is the root node of
   `test_winch.py`; nothing binds its stack. With the two relations stated
   in the class body and nothing reaching either end, `_refuse()` raises
   `UnreachedCoordinate` at the end of the winch's simulate phase and the
   whole winch suite errors. The `if turn is None: ... = 0.0` line above
   is the remedy that touches no test — a winch nobody is driving stands
   still, which is what it does today (`paid = winch.line.value; if paid
   is None: paid = 0.0`). Same shape as openarm's "`ArmsAtRest` keeps two
   zero bindings so the gripper relation has a source". If the
   orchestrator would rather have the rest value in the test than in the
   model, the alternative is one line in `WinchTest` and no `if` in
   `winch.py` — that is a test change and therefore not mine to make.

3. **A joint declared on a shared leaf carries its parent's placement
   numbers** (already recorded, from poseidon and OpenMANIPULATOR-X).
   `MotorGear` and `RollerBearing` are leaves whose axis and anchor are
   the *winch's* knowledge, and `RotorABC`/`RotorD` restate the
   `SANDWICH_*` matrix that `render()` also passes to `place()`. Here it
   costs nothing beyond the restatement — the four winch frames share one
   shaft axis, so one declaration serves all four — and the own-placed-
   origin anchor mode would remove the two rotor `at=` arguments. Not a
   deferral.

4. **The mover's position is a prescribed law, not a relation, and that is
   correct.** Physically the winches drive the mover; the model prescribes
   the mover and derives the line lengths, because that is what a maker
   drives and what the firmware's anchor table is written for.
   `|anchor - (x, y, z)|` is a function of three coordinates and is not
   affine, so it is neither a derived coordinate (`+`, `-` and scaling
   only) nor a `law=` (a law relates one coordinate to one coordinate).
   The four bindings stay in `Hangprinter.simulate()`. This is not a
   missing primitive but the shape of a cable robot's inverse kinematics,
   and it is the same in kossel and hexapod. Nothing about it is
   hand-written *frame* arithmetic: it is the machine's own equation.

5. **Not a gap, but the reason this project is not deferred**: the mover
   has three freedoms against the ceiling, and "several joints on one body
   compose in binding order" is the primitive OpenCycloid, the hexapod and
   YouCanBuildDog are deferred for. Three orthogonal *translations* commute,
   so every composition order gives the same body placement and the same
   published numbers. Worth recording as the one case where the
   composition-order gap provably cannot bite — and as evidence that a
   stated declaration-order composition would cover it for free.

## Pre-existing state

The repository is on branch `version_4` with a **clean working tree**
(`git status --porcelain` empty) at `918d491 fix(simulation): run the
belts with their gears`. There is nothing for stage 0 to commit; the
implementer starts at stage A.

## Tests

The suite is `solid test --faceted simulation/hangprinter.py` (the
declared model is `simulation.hangprinter:Hangprinter`) plus
`simulation/test_winch.py`, whose node is `WinchABC`. Both are
`solid_node.test.TestCase` suites; `HangprinterScenarioTest` is a
`ScenarioTest`. No test imports a moved name, so stage A's import fix
touches no test file.

`test_hangprinter.py` — 17 tests:

- `test_the_constants_are_the_designs`, `test_every_import_stands_where_
  the_design_puts_it`, `test_primitives_stand_where_the_design_puts_them`,
  `test_module_parts_stand_where_the_design_puts_them`,
  `test_the_nozzle_hangs_where_the_design_puts_it`,
  `test_the_alternative_toolhead`, `test_the_strands_match_the_designs_
  lines`, `test_the_runs_join_the_stubs_to_the_anchors`,
  `test_solid_integrity` — geometry at rest; untouched by this change.
- `test_a_pose_moves_only_the_mover_end`, `test_line_lengths_follow_the_
  mover`, `test_the_mover_moves_as_one`, `test_assembly_integrity` — pose
  the machine with `set_state` and measure the mover and the strands.
  These are what prove the three prismatics are the old `translate`.
- `test_the_stacks_turn_by_the_line_they_pay_out` — measures each spool
  gear, motor gear and both rollers about **their own placed axes**
  against `advantage · ΔL / Spool_r`, `255/20` of it, and
  `-pitch/roller` of it. This is the test that proves every sign in the
  ratios above; if `SENSE` or `BELT_SENSE` is wrong it fails here first,
  and the fix is to flip the declared axis or the constant, never to
  re-introduce a per-instant `_sign`.
- `test_the_belt_travels_with_its_gear` — asserts
  `abs(winch.belt.travel.value) == radians(turn) * pitch_radius` within
  0.01 mm. The port stays; the value now arrives through
  `ratio=BELT_SENSE * BELT_MM_PER_DEGREE`, whose multiplication order
  differs from today's `radians * SPOOL_PITCH_RADIUS`, so expect a
  last-bit (~1e-16 relative) difference in the published expression. Far
  inside the 0.01 tolerance, and `capture_poses` rounds ports to 9
  decimals, so it should not even show in the comparison.
- `test_the_teeth_ride_together`, `test_the_sense_pays_out` — the belt's
  phase against the gears' teeth, and that lengthening A's line turns
  winch A the way the line leaves the spool. Both depend on
  `spool_sense()` keeping today's answer.

`test_winch.py` — 5 tests, all on a lone `WinchABC`:
`test_the_belt_rides_its_three_circles`,
`test_the_belt_turns_on_the_roller_between_gear_and_motor`,
`test_the_belt_clears_the_parts_around_it`, `test_solid_integrity`,
`test_assembly_integrity`.

`HangprinterScenarioTest` — 2 tests: `test_homing_one_coordinate_holds_
the_others` and `test_the_instructions_move_the_mover_without_collision`
(`meshes = True`, interference sampled every second along eight
instructions).

**Flagged, decision the orchestrator's, not the implementer's:**

- `test_winch.py` (all five) is the only test the refactor can break, and
  only through gap 2 above. The proposal keeps it green by giving the
  winch a rest value in the model. The alternative — bind
  `self.node.rotor.turn = 0.0` in a `setUp`, and drop the `if` from
  `winch.py` — is cleaner in the model and is a test edit. Flagging both;
  implement the first unless told otherwise.
- No other test is expected to change. If
  `test_the_stacks_turn_by_the_line_they_pay_out` or
  `test_the_sense_pays_out` goes red, that is a wrong sign in this
  proposal, not a test that needs changing: report it and fix the
  constant.
- Whatever the baseline says: the suite has not been run against this
  framework tree, so stage A establishes it, and a test red at stage A
  stays red at stage B.
