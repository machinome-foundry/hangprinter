## 1. Layer and constants

- [ ] 1.1 `pyproject.toml`, `simulation/` package, `scad.py` (import_scad handles for the module parts, source set), `part.py` (DesignStl, ScadPart, place helper), `materials.py` (the layout's colours)
- [ ] 1.2 `layout.py`: the design's parameters and the layout's derived numbers under their own names (anchors, Sidelength, lx*, ly2, bc_x_pos, cx/cy, the winch stations, the action points); `csg.py`: the CSG export and parser used by the parity tests
- [ ] 1.3 `test_layout.py` red: the Python constants against the design's `echo` of the same expressions

## 2. Ceiling unit (ceiling-unit-layout, spool-drive)

- [ ] 2.1 Winch: rotor stack, covers, rod, bracket, motor and encoder, motor gear (mirrored by flag), roller bearings; ABC and D variants; parity contract red (brackets at the winch origin), then green
- [ ] 2.2 Deflectors, verticalizers, wire rewinder, landing brackets, ODrives, plate; parity contract for every ceiling import green
- [ ] 2.3 Belt: three-circle wrap with `travel` port; riding and exact-clearance contracts red (two-circle loop), then green
- [ ] 2.4 Internal strands from the layout's endpoints; internal-line parity green

## 3. Mover and anchors (mover-assembly, anchor-station)

- [ ] 3.1 Beams, markers, clamps, clay extruder and holders, alternative toolhead under `clay`; parity and tip-height contracts red (no toolhead offset), then green
- [ ] 3.2 Anchor plates, towers (body 0), assembled bullets; parity green

## 4. Kinematics (line-kinematics, line-path, spool-drive)

- [ ] 4.1 Root drivers; mover placed; D and anchor strands with ports bound by the root; strand parity at a pose red (strands vertical), then green
- [ ] 4.2 Ceiling runs to the anchors' low action points; continuity contract
- [ ] 4.3 Winch `line` ports; spool sense from the exit direction; stack, gear, belt phase and roller rotation; turning contracts red (no rotation), then green
- [ ] 4.4 Instructions; scenario sweep with interference and bed/ceiling clearance sampled

## 5. Evidence and record

- [ ] 5.1 Root integrity contracts; mutation check (drop the toolhead offset from the D length, flip the spool sense, drop the mirror on winch A's gear, misplace the roller) and note which contract catches each
- [ ] 5.2 `solid build`; read `viewer.json` (drivers, instructions, flexible specs, pieces); snapshots at the origin and at a lifted pose; exact run of every test file
- [ ] 5.3 README section on the simulation; archive the change, fill `Purpose` in every spec; commit
