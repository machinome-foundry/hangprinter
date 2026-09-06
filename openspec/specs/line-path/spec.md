# line-path Specification

## Purpose
Where every line runs -- inside the ceiling unit, down to the floor anchors, and from the anchors and the ceiling to the mover -- so that each strand starts and ends where the design's own segments do.
## Requirements
### Requirement: The mover segments land on their action points
The model SHALL draw three D strands from the ceiling verticalizer
points `anchors[D] + R_k · (0, Sidelength/√3, 0)` for `k` in 0°, 120°,
240° down to the mover's corner points `pos + R_k · (0, Sidelength/√3,
77)`, and for each anchor `i` in A, B, C four strands from `anchors[i] +
R_i · p` to `pos + R_i · p` for `p` in the layout's `a_high_left`,
`a_low_left`, `a_high_right`, `a_low_right` (`(∓Sidelength/2,
−Sidelength/√8 + 5, 75)` and 37.2 mm below: the corner clamp's bearing
spacing 22.2 plus two 7.5 mm groove radii), `R_i` the rotation by `i ·
120°`. `Sidelength` is `beam_length + 2 · Cc_plastic_length` (444.17 mm
at 400). Every strand is 1 mm in radius.

#### Scenario: Strands match the design's segments at a pose
- **WHEN** the model is posed at `(100, −50, 200)` and the design's CSG is exported with the same mover position
- **THEN** for each of the design's fifteen mover-line cylinders there is one strand whose two end centres coincide with the cylinder's within 0.05 mm

#### Scenario: A pose change moves only the mover end
- **WHEN** the pose changes from the origin to `(300, −200, 450)`
- **THEN** every anchor-side end centre is unchanged within 0.01 mm and every mover-side end centre has moved by `(300, −200, 450)` within 0.05 mm

### Requirement: The ceiling runs reach the anchors
The model SHALL draw the ceiling unit's nineteen internal segments
where `ceiling_unit_internal_lines_v4p1()` draws them, and one run per
internal stub — two per ABC winch — from the stub's origin to that
anchor's low action point (`anchors[i] + R_i · a_low_left` for the run
nearer the winch's left line, `a_low_right` for the other).

#### Scenario: Internal segments match the design
- **WHEN** the design's CSG is exported
- **THEN** each of its nineteen internal-line cylinders has one strand whose end centres coincide with it within 0.05 mm

#### Scenario: Runs are continuous with the stubs and the anchors
- **WHEN** the model is built at the origin
- **THEN** each run starts within 0.05 mm of its stub's far end, ends within 0.05 mm of its anchor's low action point, and passes no closer than 20 mm to the ceiling plate except within 60 mm of its start

