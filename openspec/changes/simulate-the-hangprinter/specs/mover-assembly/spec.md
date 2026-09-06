## ADDED Requirements

### Requirement: The mover is the layout's mover
The model SHALL place at `pos + [0, 0, 77]`, for each corner `k` in 0°,
120°, 240° under `rotate([180, 0, k + 180])`: a `beam_length × 15 × 15`
carbon beam at `[−beam_length/2, −(Sidelength + 10.5)/√12 − √3, 0]`, two
90 mm marker discs with their posts at the layout's per-corner offsets,
and the corner clamp STL at `[0, Sidelength/√3 − Cc_action_point_from_mid,
−2.5]`; and the toolhead: with `clay` true the clay extruder STL body at
`[0, 0, −426]` with its holder at −364 and its top holder at 322, else
the shorter beam with the extruder holder, the hot end and the drive box
as the layout's `else` branch draws them.

#### Scenario: The mover matches the design
- **WHEN** the design's CSG is exported at the origin
- **THEN** the three corner clamps, the clay extruder and the three beams match the design's matrices within 0.01 mm, and the toolhead's lowest point stands at `z` 0 within 0.5 mm

#### Scenario: The alternative toolhead
- **WHEN** the model is built with `clay` false
- **THEN** the clay extruder and its holders are absent, the extruder holder, the short beam, the hot end and the drive box are present, and the hot end's tip stands at `z` 0 within 0.5 mm

### Requirement: The mover holds together and clears the frame
The beams, clamps, markers and toolhead SHALL share no volume with one
another, and the mover SHALL share no volume with the bed, the anchors or
the ceiling unit at any instruction target.

#### Scenario: Integrity across the travel
- **WHEN** the model is posed at every instruction target
- **THEN** no two printed solids share volume and every mover part is above the bed's top face
