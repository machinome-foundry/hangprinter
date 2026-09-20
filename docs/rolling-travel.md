# Rolling-travel migration evidence

The ABC and D winches still advance their belts at the spool gear pitch
circle. `BELT_MM_PER_DEGREE` now states that relation as
`machinome_mechanics.rolling_travel(1.0, SPOOL_PITCH_RADIUS)`; handedness,
shaft signs, gear ratios, and the measured spool pitch radius are unchanged.

The baseline is branch `version_4` at
`a342b94c229cce8e5334687b9f37313b6d30356e`. The first baseline import was
mistakenly run from `/home/asa/devel/machinome-studio`; Python then found the
workspace's source-only `molejo/` namespace and failed with `ImportError:
cannot import name 'P' from 'molejo'`. Repeating it from this project root,
which is the documented invocation, resolved the installed package and
succeeded. This was an invocation failure, not a model baseline failure.

Validation ran from the project root with this prefix:

```sh
export PYTHONPATH="$PWD:/home/asa/devel/machinome-studio/WTs/mechanics-rolling-travel"
```

The executables were `/home/asa/devel/machinome-studio/.venv/bin/python` and
`/home/asa/devel/machinome-studio/.venv/bin/machinome`; the latter ran
`test --faceted simulation/winch.py`, `test --faceted
simulation/hangprinter.py`, the corresponding two `--exact` commands,
`build`, and:

```sh
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot -o /tmp/hangprinter-rest.png --autocenter
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot -o /tmp/hangprinter-lift.png --autocenter --drive z=300
```

The measured pitch radius was 81.16902097686662 mm and both expressions gave
1.4166666666666665 mm/degree. At -360, -45, 0, 90, and 810 degrees their
results agreed to floating-point precision at -510, -63.75, 0, 127.5, and
1147.5 mm; the helper also accepted a symbolic `Angle()` expression. The
faceted and exact winch suites each passed 5/5; the faceted and exact root
suites each passed 19/19. The build succeeded and both snapshot files were
created. Visual inspection showed the mover raised at `z=300`, all four line
sets still joining mover and anchors, and the ceiling winches and belt routes
remaining on their recorded datums. Snapshot inspection does not prove tooth
contact, line buildup, or belt elasticity.
