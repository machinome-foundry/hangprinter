## Why

This repository is Torbjørn Ludvigsen's Hangprinter version 4: the
OpenSCAD sources and exported STLs of its printed parts, and one file,
`src/layout.scad`, that places them into the machine for a picture —
the ceiling unit with its four winches, the mover with its three carbon
beams, the three floor anchors, and the lines between them, at a handful
of hard-coded mover positions along a `$t` sweep. That picture is not a
machine. Nothing in it says how far each spool has to turn for the mover
to reach a point, the spools and motor gears do not turn, the belts are
a sketch that does not touch the belt rollers, and the lines are drawn
only where the design's author needed them for a figure: the runs from
the ceiling unit down to the floor anchors are 100 mm stubs.

What physically goes wrong today is that none of the interfaces that make
a Hangprinter a Hangprinter can be checked: whether four lines paid out
from the ceiling really put the mover where the firmware's anchor
coordinates say; whether the twelve anchor segments and three D lines
stay parallel and land on the corner clamps at every pose; whether the
GT2 loop the motor bracket's roller tensions actually rides the spool
gear, the roller and the motor gear the bracket places; whether the
mover's toolhead clears the bed and the ceiling across the travel. None
of it has been drawn as motion, so none of it can be wrong, and none of
it can be right.

## What Changes

- A solid-node project in `simulation/` that reads the design as it is
  and assembles it into the moving machine. Every part the layout
  imports as an STL is that STL (`StlNode`), every part it calls as a
  module is that module through solid2's `import_scad`, and placements
  are restated in Python in the layout's own nesting order. Only what the
  design does not draw is modelled here: the lines as flexible strands
  from the ceiling to the anchors and from both to the mover, the GT2
  belts as toothed loops on the pulleys and rollers the design places,
  the belt roller bearings, the plate, the bed, the ODrive boards, the
  carbon beams and the markers as the layout's own primitives.
- Line kinematics as the machine's drivers: `x`, `y`, `z` are the
  mover's position in the design's frame (the calibrated origin on the
  bed, Z up); the four line lengths follow from the anchor coordinates
  the layout carries, each spool turns by the line it pays out, each
  motor gear turns 255/20 as far, each belt travels with its spool gear.
- Instructions on the root: `Home` (the origin), `HomeX`, `HomeY`, `HomeZ`
  (one coordinate to zero, the others held), `Lift`, `Center`, and one
  move toward each of the anchors A, B and C at the bed's edge.
- Every part carries the colour the layout gives it, and a material
  colour where the layout gives none.
- Contracts prove the interfaces the picture leaves open: every part
  placed where the design's own CSG export places it, line segments
  parallel and landing on their action points at every pose, spool and
  motor gear turning by the paid-out line at the design's ratio, the belt
  riding its three circles and travelling with the spool gear, the mover
  clear of the bed and the ceiling, no two rigid parts sharing volume
  anywhere in the travel.

## Capabilities

### New Capabilities
- `line-kinematics`: the drivers, the four line lengths from the anchor
  coordinates, the mover's pose, and the root instructions.
- `line-path`: every drawn line — the ceiling unit's internal runs, the
  runs from the ceiling deflectors to the floor anchors, the anchor
  segments and the D lines to the mover — as strands that start and end
  where the design's own segments do.
- `spool-drive`: the spool stack turning with paid-out line, the motor
  gear turning at the gear ratio, the belt loop on spool gear, roller and
  motor gear, the roller bearings turning under it.
- `ceiling-unit-layout`: the four winches, deflectors, verticalizers,
  landing brackets, wire rewinder, ODrives and plate at the design's
  transforms, hung under anchor D.
- `mover-assembly`: the three beams, the corner clamps, the hp-mark
  markers and the toolhead — the clay extruder the layout renders, or the
  extruder holder with a hot end the layout keeps as its alternative.
- `anchor-station`: each ABC anchor's plate and two line rollers at the
  design's transform, and the action points the lines turn at.

### Modified Capabilities
- (none; this is the project's first design change)

## Impact

- New `pyproject.toml` naming `simulation.hangprinter:Hangprinter`, new
  package `simulation/` beside `src/` and `stl/`, `openspec/` as the
  design record, `README.md` gaining a section on the simulation,
  `.gitignore` covering the build directory.
- The `.scad` sources and the `.stl` exports are not edited. Where the
  model has to disagree with the layout it says so in the design and in
  a contract.
- Out of scope, recorded for a later change: the bearings inside the
  deflectors, verticalizers, rollers and corner clamps (the design's
  STLs are the holders only); the spool cores, the ziptie tensioners,
  the cable clamps, the Raspberry Pi mount, the BLTouch arm and the pen
  holders (not placed by the layout); line buildup on the spools (the
  spool radius is the design's constant); the bottom triangle; the
  encoder cables and wiring.
- Uses solid-node 0.6 with the declarative API and molejo 0.2 as
  published; no framework change is needed.
