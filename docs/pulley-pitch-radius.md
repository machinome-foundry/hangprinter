# Pulley pitch-radius migration evidence

Hangprinter's GT2 pulley flank radius and groove-passage construction now
derive their flat pitch circle with `machinome_mechanics.pulley_pitch_radius`.
`pulley_radius` still subtracts the 0.254 mm pitch-line surface allowance,
and `_passage` still receives the loop's fitted period; no tooth count,
rounding, fit, belt route, sign, or control changed. Independent test
arithmetic remained the oracle.

The clean base was `version_4` at
`d0c32e07b77a1c59bc9bab220043938b4c0d2008`. Commands ran from the project
root with:

```sh
export PYTHONPATH="$PWD:/home/asa/devel/machinome-studio/WTs/mechanics-pulley-pitch-radius"
```

and the workspace Python/machinome executables. The pre-edit probe confirmed
nominal pitch radii 6.366197723675814 mm (20 teeth) and 81.16902097686662 mm
(255 teeth), with the existing allowance producing flank radii
6.1121977236758145 and 80.91502097686661 mm. Pre-edit faceted suites passed
5/5 for the winch and 19/19 for the root.

The final probe compared old and shared formulas for 20 and 255 teeth at
nominal 2 mm pitch, both counts at the actual fitted period
1.9978496683445934 mm, and 7 teeth at 2.5 mm. All pitch radii matched exactly.
At the fitted period they remained 6.359353005430915 and 81.08175081924416
mm, while `pulley_radius` preserved the allowance at 6.105353005430915 and
80.82775081924416 mm. A deferred pitch
`solid2.get_animation_time() * 2` produced
`(20 * ($t * 2.0)) / 6.283185307179586`, a deferred radius from 0 to
6.366197723675814 mm. Validation commands were:

```sh
/home/asa/devel/machinome-studio/.venv/bin/machinome test --mesh simulation/winch.py
/home/asa/devel/machinome-studio/.venv/bin/machinome test --mesh simulation/hangprinter.py
/home/asa/devel/machinome-studio/.venv/bin/machinome test --brep simulation/winch.py
/home/asa/devel/machinome-studio/.venv/bin/machinome test --brep simulation/hangprinter.py
/home/asa/devel/machinome-studio/.venv/bin/machinome build
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot -o /tmp/hangprinter-pulley-rest.png --autocenter
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot -o /tmp/hangprinter-pulley-lift.png --autocenter --drive z=300
```

Faceted and exact suites each passed 5/5 for the winch and 19/19 for the
root; build and both snapshots succeeded. Visual inspection found the same
whole-machine rest and raised-mover poses, with line endpoints, winch station,
and visible routes unchanged. The contracts cover only the modeled motion and
geometry, including the fitted tooth geometry; neither those contracts nor
the overview pixels certify force, belt tension, or elasticity.

The mechanics worktree base planning commit was
`4870f32379fc9e0c966a0466a7a84f1ce4743ae5`; it did not contain the tested
implementation. The uncommitted `machinome_mechanics/belts.py` code identity
was SHA-256
`63f8d30a19d36b2cc4504919d6e3b989df1c0092348ad4c1930b31adb4ea482d`.
Framework HEAD stayed `0ce71cdea6cc4a2e7fd7e85dc68847daef3d34cc`.
Viewer HEAD changed concurrently from
`5dcbf4d476ff0d34bb42fe13f9b799ebd8ec5852` to
`4355da1a7f64dacd7d86eb27dbdfdf7ced94598f` and its worktree was dirty with
unrelated retained-time work; this project neither changed nor pinned it.
