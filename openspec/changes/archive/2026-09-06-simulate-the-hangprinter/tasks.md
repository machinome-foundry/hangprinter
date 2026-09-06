## 1. Layer and constants

- [x] 1.1 `pyproject.toml`, `simulation/` package, `scad.py` (import_scad handles for the module parts, source set), `part.py` (DesignStl, ScadPart, place helper), `materials.py` (the layout's colours)
- [x] 1.2 `layout.py`: the design's parameters and the layout's derived numbers under their own names (anchors, Sidelength, lx*, ly2, bc_x_pos, cx/cy, the winch stations, the action points); `csg.py`: the CSG export and parser used by the parity tests
- [x] 1.3 `test_hangprinter.py` constants contract red: the Python constants against the design's `echo` of the same expressions (`layout.py` defines no node, so the contract lives with the root's)

## 2. Ceiling unit (ceiling-unit-layout, spool-drive)

- [x] 2.1 Winch: rotor stack, covers, rod, bracket, motor and encoder, motor gear (mirrored by flag), roller bearings; ABC and D variants; parity contract red (brackets at the winch origin), then green
- [x] 2.2 Deflectors, verticalizers, wire rewinder, landing brackets, ODrives, plate; parity contract for every ceiling import green
- [x] 2.3 Belt: three-circle wrap with `travel` port; riding and exact-clearance contracts red (two-circle loop), then green
- [x] 2.4 Internal strands from the layout's endpoints; internal-line parity green

## 3. Mover and anchors (mover-assembly, anchor-station)

- [x] 3.1 Beams, markers, clamps, clay extruder and holders, alternative toolhead under `clay`; parity and tip-height contracts red (no toolhead offset), then green
- [x] 3.2 Anchor plates, towers (body 0), assembled bullets; parity green

## 4. Kinematics (line-kinematics, line-path, spool-drive)

- [x] 4.1 Root drivers; mover placed; D and anchor strands with ports bound by the root; strand parity at a pose red (strands vertical), then green
- [x] 4.2 Ceiling runs to the anchors' low action points; continuity contract
- [x] 4.3 Winch `line` ports; spool sense from the exit direction; stack, gear, belt phase and roller rotation; turning contracts red (no rotation), then green
- [x] 4.4 Instructions; scenario sweep with interference and bed/ceiling clearance sampled

## 5. Evidence and record

- [x] 5.1 Root integrity contracts; mutation check: the D length without the toolhead lift is caught by the stack-turn contract (and the parity contract, since winch D then turns at the origin); the spool sense flipped by the pay-out and stack-turn contracts; winch A's gear placed unmirrored by the parity contract (the leaf unmirrored is stopped earlier, by `place()`'s guard); the roller 3 mm high by the belt riding and turning contracts and the primitives' parity
- [x] 5.2 `solid build`; read `viewer.json` (drivers, instructions, flexible specs, pieces); snapshots at the origin and at a lifted pose; exact run of every test file
- [x] 5.3 README section on the simulation; archive the change, fill `Purpose` in every spec; commit
