## ADDED Requirements

### Requirement: Spools turn by the line they pay out
Each winch SHALL turn its spool stack (spool gear, spools, separator
disc) about the sandwich axis by `advantage · (L − L₀) / Spool_r`
radians, `Spool_r` 75 mm, `advantage` 2 for A, B, C and 1 for D, `L₀`
the line length at the origin, in the sense that moves the spool's
bottom along the first internal segment when `L` grows; the motor gear
SHALL turn the same sense `255/20` times as far about its own axis.

#### Scenario: A pose change turns the stacks
- **WHEN** the pose changes from the origin to `(300, −200, 450)`
- **THEN** each spool gear has turned about its axis by the test's own `advantage · ΔL / 75` radians within 0.01°, each motor gear by 12.75 times that within 0.05°, and the covers, brackets and rods have not moved

#### Scenario: The sense pays out
- **WHEN** anchor A's line grows by 100 mm
- **THEN** a point on winch A's spool at the line's tangent moves along the exit direction of the first internal segment, not against it

### Requirement: The belt rides its three circles
Each winch SHALL draw a GT2 belt (6.5 mm wide, 1.38 thick, 2 mm pitch,
teeth inward) as a closed loop around the spool gear's pitch circle
(radius `255 · 2 / 2π` at the sandwich axis), the belt roller (5 mm
bearing radius plus 1.004 mm tooth reach, at `(Belt_roller_bearing_xpos,
Belt_roller_h − Depth_of_roller_base/2)` in the winch's belt plane,
bent backwards) and the motor gear's pitch circle (`20 · 2 / 2π` at the
bracket's shaft position), centred on the spool gear's width, with 301
teeth.

#### Scenario: The belt touches all three
- **WHEN** the model is built at the origin
- **THEN** on every winch the belt's crests stand on the spool gear's and the motor gear's flank circles (pitch radius less 1.004 mm) within 0.1 mm, its back rides the roller's 5 mm rim within 0.1 mm, the run from the gear to the roller is within 3° of vertical and the run from the roller to the motor gear level with the roller's rim within 0.2 mm; and the belt shares no volume with the motor, the encoder or the rod, and at most 0.25 mm³ with each spool cover (the cover's rim rail sits in the belt's path where it leaves the gear: 0.19 mm³ as designed)

#### Scenario: The belt travels with the spool gear
- **WHEN** anchor A's spool gear turns by half a tooth (180/255 degrees)
- **THEN** the belt's tooth pattern on the gear's arc has moved half a pitch the gear's way, the roller bearings have turned the opposite sense at the belt's speed over their 5 mm rim within 0.1°, and the belt's `travel` port carries the spool gear's pitch-line travel

#### Scenario: The teeth ride together along a move
- **WHEN** the mover rises 2 mm in eight steps (about one motor-gear tooth on winch D)
- **THEN** on every winch the volume the belt shares with the motor gear and with the spool gear swings by less than 3 mm³ over the steps; teeth sweeping through each other would swing it 33 mm³, two cycles per tooth
