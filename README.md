Hangprinter ![Hangprinter logo](./hangprinter_logo_blue_50.png)
===========

Welcome to the Hangprinter repository!

This branch contains Hangprinter version 4.
Breaking changes might occur from time to time.

For more general information about the Hangprinter Project, refer to [hangprinter.org](https://hangprinter.org).

Documentation
----------------
Start here: [hangprinter.org/doc/v4](https://hangprinter.org/doc/v4/).


Using letter sized paper for the layout?
-------------------------
You can specify that in a make-call:
```
make layout_letter.pdf
```

The `make` call will require Cairosvg, sed, and Ghostscript to work.
Already installed on many standard GNU/Linux systems.

Simulation
----------

`simulation/` reads the version 4 design above into the whole machine,
as a [solid-node](https://pypi.org/project/solid-node/) project: every
part `src/layout.scad` imports as an STL is that file, every part it
calls as a module is that module through solid2's `import_scad`, and its
placements are restated in Python in the layout's own nesting order and
checked against the layout's own CSG export.  Only what the design does
not draw is modelled there: the lines as strands from the ceiling unit
to the floor anchors and from both to the mover, the four GT2 belts as
toothed loops on the spool gear, the belt roller and the motor gear the
bracket places, the roller bearings, the plate, the bed, the ODrives,
the beams and the hp-mark markers.  The `.scad` sources and the `.stl`
exports are not edited.  The design record is `openspec/`.

    solid build                                  # publish the model into _build/
    solid test --faceted simulation/hangprinter.py   # the machine's contracts, fast
    solid test simulation/hangprinter.py         # the same, decided exactly
    solid test simulation/winch.py:WinchABC      # one winch's belt and stack
    solid build --set clay=false                 # the hot-end toolhead instead of the clay extruder

The drivers are the mover's position: `x`, `y` in millimetres from the
calibrated origin, `z` above it, in the frame `layout.scad` draws the
machine in.  The four line lengths follow from the layout's anchor
table, each spool turns by the line it pays out (twice the anchor
distance on A, B and C, whose lines run anchor to mover and back; once
on D), each motor gear turns 255/20 as far, each belt travels with its
spool gear and the roller bearings turn under it, and fifteen strands
are redrawn to the mover.  The instructions `Home`, `HomeX`, `HomeY`,
`HomeZ`, `Center`, `Lift`, `AnchorA`, `AnchorB` and `AnchorC` move it.

Knobs (`--set`): `beam_length` (400, the design's `Beam_length`, which
moves the corner clamps, the verticalizers and every line's action
point through `Sidelength`); `clay` (true: the 3D Potter ram extruder
the layout renders; false: the extruder holder with the layout's
stand-in hot end and drive).

What the model found in the design, recorded in `openspec/`:

* The layout hangs the ceiling unit under anchor D 33 mm up and draws
  the ceiling's internal lines 43 mm up, without anchor D's 21.85 mm X
  offset; the model draws both where the layout does.
* The spool covers' rim rails sit in the belt's path where it leaves
  the gear (0.19 mm³ each); the render motor's encoder board sits in
  the bracket (up to 2 mm³); the D spool's halves, placed 9 mm apart,
  share 5.2 mm³; the clay extruder's 40-gon tube shares 7 mm³ with its
  holder's 60-gon ring; the beams' end corners cut 0.1 mm³ into the
  clamps' rounded pockets; the design's own `bullet()` seats the
  anchor's bullet 1 mm (131 mm³) into the tower's sleeve.  Each is an
  allowance stated in the contracts, none a clearance.
* The layout's belt is a sketch from an earlier bracket: its strips pass
  10 mm under the roller.  With the roller where the bracket puts it
  the belt leaves the spool gear straight down, turns on the roller and
  runs level onto the motor gear, 303 teeth, 606 mm, 2 degrees off
  vertical because the roller is placed at the gear's outer diameter
  plus 1.4 rather than at the belt's back.
* The hp-mark markers are drawn as a disc, a block through the beam and
  a pin through both; the model draws the block as a clip with the
  beam's section and the pin's hole taken out of it.  The stand-in
  drive box is drawn through the hot end and gets a bore for it.
* `new_tilted_line_deflector.stl`, `line_roller_anchor.stl` and
  `extruder_holder.stl` are print packs, and the layout renders them
  laid out for the printer: the deflector's bearing sticks and the
  anchor's bullet lie beside their holders.  The model takes the holder
  bodies, draws the bullet assembled with `bullet()`, and leaves the
  sticks out (no assembled position is stated).  The spool covers' 30
  to 82 loose 2 mm³ shells and the ram extruder's four inside-out
  shells are left out too.
* The `stls` condition on the ram extruder's holders is inverted
  (module when STLs are wanted); the model uses the modules.

Not drawn: the bearings inside the printed line guides, the spool
cores, the ziptie tensioners, cable clamps, Pi mount, BLTouch arm and
pen holders (not placed by the layout); line buildup on the spools (the
line winds at `Spool_r`); the bottom triangle; wiring; the "ODrive"
lettering cut through the boards (its counters would be loose bodies).

Contributing Improvements
-------------------------
We're super grateful for merge request.
Please submit to this repo on Gitlab.

The second best option for contributing improvements is to make an issue on Gitlab.

Lead Dev
---------------------------------
[tobben](https://torbjornludvigsen.com).

Campaign
---------------------------------
[Github Sponsors](https://github.com/sponsors/tobbelobb/)

Merchandise
---------------------------------
[Spreadshirt link for Sweden](https://shop.spreadshirt.se/hangprinter-merchandise/).
[Spreadshirt link for US](https://shop.spreadshirt.com/hangprinter-merchandise/).

Credits
-------
See [contributors](https://gitlab.com/tobben/hangprinter/graphs/version_4) for committer stats.
Note that almost all ideas implemented by the commits have come up in conversations among fellow Reprappers.
Thanks!

List sorted alphabetically.
