## ADDED Requirements

### Requirement: The ceiling unit stands where the design places it
The model SHALL place under anchor D, through `translate(anchors[D] +
[0, 0, 33]) rotate([180, 0, 0])`, every STL and module `full_winch()`
places — four motor brackets, four motors with their encoder boards and
motor gears, the ABC spool stacks and covers, the D stack and covers,
the smooth rods, the belt roller bearings, the A deflector and the B and
C line guides, three verticalizers, five horizontal deflectors, the wire
rewinder, three landing brackets, two ODrives and the plate — and the
internal lines through `translate([0, 0, 43 + anchors[D].z])
rotate([180, 0, 0])`.

#### Scenario: Every imported STL matches the design's matrix
- **WHEN** the design's CSG is exported and its `import` nodes are read with their composed matrices
- **THEN** for each of the 51 ceiling and mover imports there is exactly one node in the model on the same file (or, for a print pack, on its named body) whose world vertices coincide with the file's vertices under the design's matrix within 0.01 mm, and the mirrored motors, gears and line guide match under their mirrored matrices

#### Scenario: Module parts and primitives match the design
- **WHEN** the same CSG is read for its `cube` and `cylinder` nodes
- **THEN** the plate, the smooth rods, the beams, the marker discs and the bed have one node each whose bounds coincide with the design's within 0.01 mm

### Requirement: The winch parts hold together
Each winch's rotating stack SHALL be one body per part, each cover shall
be its main body, and the bracket, motor, gear, rod, roller bearings and
covers SHALL share no volume with one another or with the stack.

#### Scenario: Integrity of the ceiling unit
- **WHEN** the model is built at the origin
- **THEN** every printed solid of the ceiling unit is one body and no two of them share volume
