# line-kinematics Specification

## Purpose
What the four lines have to do for the mover to be at a point: the drivers, the anchor distances the layout's table gives, and the moves the machine offers.
## Requirements
### Requirement: The mover position drives the lines
The root SHALL declare drivers `x` and `y` (mm from the calibrated
origin, range ±400) and `z` (mm above it, range 0 to 1200), and place
the mover with its reference point -- the hot end's tip, 77 mm under the
corner triangle -- at `(x, y, z)` within 0.05 mm.
The line length of anchor `i` in A, B, C SHALL be `|anchors[i] − (x, y,
z)|` and of D `|anchors[D] − (x, y, z + 77)|`, with `anchors` the
layout's table (A `(16.83, −1584.86, −463.17)`, B `(1290.18, 1229.19,
−507.45)`, C `(−1409.88, 742.61, −501.80)`, D `(21.85, −0.16,
1993.67)`) and 77 the layout's `length_of_toolhead`.

#### Scenario: The origin
- **WHEN** the drivers are bound to `x` 0, `y` 0, `z` 0
- **THEN** the mover's corner action points stand at the layout's `mover([0,0,0])` positions within 0.05 mm and every segment to an anchor is the test's own `|anchor − pos|` long within 0.05 mm

#### Scenario: An off-centre pose
- **WHEN** the drivers are bound to `x` 300, `y` −200, `z` 450
- **THEN** every mover part has moved by exactly `(300, −200, 450)` from its origin position within 0.01 mm, and each anchor's segments are the test's own length within 0.05 mm

### Requirement: Instructions position the mover
The root SHALL declare `Home` (`x` 0, `y` 0, `z` 0), `HomeX`, `HomeY`
and `HomeZ` (that one coordinate to 0, the others held), `Center` (`x`
0, `y` 0, `z` 400), `Lift` (`z` 900, `x` and `y` held), and `AnchorA`,
`AnchorB`, `AnchorC` (350 mm from the origin toward that anchor's
azimuth, `z` 60).

#### Scenario: Homing one coordinate holds the others
- **WHEN** a simulation triggers `AnchorB`, then `Lift`, then `HomeX`
- **THEN** after the ramps `x` is 0 within 0.01 mm, `y` is `AnchorB`'s and `z` is 900

#### Scenario: No interference along the moves
- **WHEN** a simulation triggers `Lift`, `AnchorA`, `AnchorB`, `AnchorC`, `Center`, `HomeZ`, `HomeX`, `HomeY` in turn, sampling every 1 s
- **THEN** no two rigid solids share volume at any sample beyond the design's own stated allowances, and the mover stays above the bed's top face and below the ceiling plate

