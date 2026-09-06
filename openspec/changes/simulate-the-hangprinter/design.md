## Context

A Hangprinter is a cable robot: a triangular mover hangs from four
lines, three of them (A, B, C) running from winches on a ceiling unit
down to anchors on the floor and from there to the mover's corners, and
the fourth (D) running from the same ceiling unit straight down to the
corners. Moving the mover means paying out and taking in line on four
spools; no axis of the machine is an axis of the print. The repository
draws the printed parts and, in `src/layout.scad`, the machine at rest
for a figure. This change reads that figure into a machine that moves.

The model is a solid-node project on the declarative node API. It is a
layer over the design, as thin as the design allows:

- A part the layout imports as an STL is an `StlNode` on that file
  (`stl/`). Five of those files are print packs — several bodies laid out
  for the printer — and there the node names the body the layout means.
- A part the layout calls as a module is a `Solid2Node` calling that
  module through solid2's `import_scad`. Each such node adds the whole
  `src/` and `stl/` set to its source set so an edit there rebuilds it.
- `src/layout.scad` itself cannot be imported: solid2's parser refuses
  its `data_collection_positions_standard` table (line 808). Its
  placements are restated in `simulation/layout.py` under the design's
  own names, in the design's own nesting order, and checked against the
  design's CSG export (`openscad -o layout.csg`), which lists every
  primitive with its composed matrix in a tenth of a second and needs no
  geometry evaluation.
- Lines and belts are molejo shapes. The design draws lines as 1 mm
  cylinders; the strands keep that radius.

## Coordinates

The design's frame is kept whole: the origin is the calibrated nozzle
origin on the bed, Z is up, and the anchor coordinates are the layout's
`anchors` table (the firmware's, less the 350 mm the clay extruder adds
to the toolhead height). The ceiling unit is drawn in its own frame, Z up
off the plate, and hung under anchor D by the layout's own transform:
`translate(anchors[D] + [0, 0, 33]) rotate([180, 0, 0])`. The layout draws
the ceiling's internal lines under a different transform,
`translate([0, 0, 43 + anchors[D].z]) rotate([180, 0, 0])`, ten
millimetres higher and without anchor D's 21.85 mm X offset; both are
kept as drawn, and the difference is recorded below.

The drivers are the mover's position: `x`, `y` in millimetres from the
origin, `z` above it. The mover stays level; the lines are a parallel
mechanism and the design assumes no rotation.

## Goals / Non-Goals

**Goals:**
- Every part the layout places is a node, at the layout's transform, with
  the layout's colour where it gives one and a material colour where it
  does not.
- The machine moves the way the printer does: a point becomes four line
  lengths, four spool angles, four motor gear angles, four belt phases,
  and fifteen redrawn strands, and every rigid part stays out of every
  other at every pose the instructions reach.
- The runs the layout leaves as stubs — ceiling deflectors to floor
  anchors — are drawn in full.

**Non-Goals:**
- Editing the OpenSCAD design or its STLs. Disagreements are recorded,
  not fixed.
- Line buildup on the spools. The firmware compensates for it; the model
  winds line at the spool core radius `Spool_r` the design declares.
- The bearings inside the printed line guides, the spool cores and the
  small parts the layout does not place.
- The mover's rotation and the lines' sag and stretch.
- Belt tension: the loop is drawn at the pitch the three circles give it.

## Decisions

**The parity reference is the design's CSG export, not a render.** This
OpenSCAD (2021.01) has no lazy union, so rendering `full_winch()` would
union four 255-tooth gears and forty STLs through CGAL. The CSG export
writes the same tree as `multmatrix`, `import`, `cube` and `cylinder`
nodes without evaluating any geometry, and `-D` overrides the mover
position table so the design can be asked for any pose. A test walks
that tree, composes the matrices, and for every STL and every line the
design draws finds the node in the model whose file and transform match.
Rejected: comparing rendered meshes (minutes per pose, and a union hides
which part moved) and trusting the restated arithmetic by reading it
(the point of the test is that nobody has to).

**Mirrored parts are mirrored in the leaf, never in the placement.** The
layout mirrors the motor and its gear on winches A and B and the line
guide on winch B. solid-node has rotate and translate only, so a mirrored
part's node mirrors its mesh in `adjust()` (a `Flag` in its identity) and
its placement is the layout's with the mirror pushed through: X
translations negated, Y and Z rotations reversed. The CSG comparison
checks the result, matrix against matrix.

**Print packs name their body.** `new_tilted_line_deflector.stl`,
`line_roller_anchor.stl`, `extruder_holder.stl`, `whitelabel_motor.stl`
and `ram_1000_3dpotter.stl` hold several bodies. The layout imports each
whole, so its figure shows the deflector's two bearing sticks and the
anchor's bullet lying beside their holders in print layout. The model
takes the holder body, draws the anchor's bullet assembled through the
design's own `bullet()` module, and leaves the deflector's sticks out
(the design states no assembled position for them). The motor's encoder
board and the clay extruder's nozzle body are bodies of their own and
become nodes of their own. The spool covers' 30 to 82 loose shells of
about 2 mm³ at their rims are left out with the main body selected; they
are the covers' snap ridges, exported disconnected from the wall.

**Line topology and mechanical advantage are read off the drawing.** The
layout draws three D segments, one per corner, and four ABC segments per
anchor: two corners, each with a high and a low line 30 mm apart. Two
lines leave each ABC winch (the spool and its mirrored twin) and two
runs reach each anchor, so each ABC line is taken to run ceiling → anchor
low roller → mover corner → anchor high roller, and an ABC spool pays out
two millimetres of line per millimetre the anchor distance grows;
the D spool pays out one. The anchor distance is `|anchor − pos|` for A,
B, C and `|anchor − pos − [0, 0, 77]|` for D, exactly the segments the
layout draws, since both ends of every segment carry the same offset.

**Spool sense follows the line's exit.** Each spool's line leaves it
tangent at the bottom, at `Spool_r` below the axis, in the direction the
first internal segment runs; paying out means the bottom of the spool
moves that way, so the sense of rotation about the sandwich axis is the
sign of `(down × exit) · axis`, computed per winch rather than stated.
The motor gear turns the same way `Spool_teeth / Motor_teeth` (255/20)
times as far, the belt's phase advances by the spool gear's pitch-line
travel, and the roller bearings turn the other way at their own radius.

**The belt is a three-circle wrap.** The bracket places a pair of 623
bearings 87.8 mm from the spool axis at 47 mm height, inside the loop's
lower span, 7 mm above where a two-pulley loop would run: a tensioner
pushing the span out of the loop, so the belt bends backwards over it and
its teeth ride the bearing. The loop is spool gear (255 teeth at the
pitch radius its count gives), roller (5 mm plus the tooth tips' reach,
concave), motor gear (20 teeth), 301 teeth, 602.5 mm at 2 mm pitch. The
layout's own `belt()` is a sketch from an earlier bracket — its strips
pass 10 mm under the roller and a 45 mm vertical strip lands inside the
spool gear — and is not reproduced. The motor gear STL's toothed band is
centred 0.7 mm off the belt plane (its 16 mm length is placed by a 7.4
mm tooth width the file does not have); the belt is drawn in the plane
the design's belt occupies, centred on the spool gear.

**Knobs.** `beam_length` (400, the design's `Beam_length`) moves the
mover's beams, the corner clamps, the verticalizers and every action
point through `Sidelength`; `clay` (true, the layout's
`ram_1000_3dpotter`) selects the toolhead. The anchor coordinates are a
calibration of one machine and stay constants in `layout.py`, as they
are in the design.

**Design findings, kept as drawn:**
- The ceiling's internal lines are hung 10 mm above the ceiling unit and
  without its 21.85 mm X offset (the two transforms above). The model
  draws them where the design does; the CSG comparison holds either way.
- The ram extruder branch of `mover()` has its `stls` condition inverted
  for the two holders (module when STLs are wanted, STL otherwise). The
  model uses the modules, which is what the layout renders by default.
- `ram_1000_3dpotter.stl` carries four inverted shells of −11.5 mm³
  (the NEMA 23 screw holes exported inside out); they are not bodies of
  the model.
- `landing_brackets.stl` is a print pack of the three brackets; the
  layout calls the modules, and so does the model.
- The winch's `Spool_r` (75) is where the design's internal lines are
  tangent to the spools (`hz = Gap + Sep_disc_radius − Spool_r` above the
  plate); the line therefore winds at 75 mm, which is what the kinematics
  uses.

## Risks / Trade-offs

- The STL parts are faceted, so contracts between them are decided on
  meshes on either kernel; the exact kernel decides only the strands and
  belts against each other. All shipped STLs the layout uses are
  watertight (checked with trimesh), so the framework's spatial
  assertions accept them.
- The 255-tooth spool gear STL has 27 728 faces and appears four times;
  spatial contracts against it are slow. The belt-riding contracts
  measure against the pitch circles the design's numbers give rather
  than against the gear mesh, and the interference sweep is sampled at a
  coarse cadence.
- The ceiling-to-anchor runs are the model's own straight lines between
  the layout's stub origins and the anchors' low action points; the
  design does not draw them, so there is nothing to compare them to but
  their endpoints.
