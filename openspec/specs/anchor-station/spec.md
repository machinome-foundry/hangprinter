# anchor-station Specification

## Purpose
Where each floor anchor's plate and line rollers stand and where its lines turn, as the layout's ABC_anchors() places them.
## Requirements
### Requirement: The anchors stand where the design places them
For each anchor `i` in A, B, C the model SHALL place, through
`translate(anchors[i]) rotate([0, 0, i · 120]) translate([0,
−Sidelength/√8 + 5, 27]) rotate([0, 0, −90])`, a 50 × 500 × 8 plate
at `[0, −250, −8]` and two line roller towers at `[26, ±(250 − 27.91),
0]` (the lower one mirrored in Y) under `rotate([0, 0, −90])`, each
with its bullet drawn assembled by the design's `bullet()` module.

#### Scenario: The roller towers match the design
- **WHEN** the design's CSG is exported
- **THEN** each of the six `line_roller_anchor.stl` imports has one tower node whose vertices coincide with the file's tower body under the design's matrix within 0.01 mm

#### Scenario: The lines turn at the towers
- **WHEN** the model is built at the origin
- **THEN** each anchor's four segment ends and two run ends lie within 40 mm of one of that anchor's two towers, the plate and the towers share no volume, and each bullet shares at most 131 mm³ with its tower (the design's `bullet()` seats it 1 mm into the sleeve's back wall)

