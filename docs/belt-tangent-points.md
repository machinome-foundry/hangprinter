# Belt tangent-point migration evidence

Hangprinter's GT2 loop now obtains each directed contact pair from
`machinome_mechanics.belt_tangent_points`.  The local `_tangents` adapter
retains the loop's clockwise/default and counterclockwise/back-idler markers,
recovers the common normal needed by wrap and station bookkeeping, and keeps
the old left-perpendicular normal when both radii are zero.  Fitted pitch,
tooth phase, span and arc ordering, stations, controls, and surface allowances
did not change.

The clean base was branch `version_4` at
`2cc703793e9029e19313b22a00472be030173e69`.  Commands ran from the project
root with the workspace executables and this source overlay (no shared install
was changed):

```sh
export PYTHONPATH="$PWD:/home/asa/devel/machinome-studio/WTs/mechanics-belt-tangent-points"
/home/asa/devel/machinome-studio/.venv/bin/python - <<'PY'
import math
from simulation import gt2
from simulation.winch import belt_circles

def sense(circle):
    return -1.0 if circle.get('turn') == 'counterclockwise' else 1.0

def old_normals(circles):
    result = []
    for index, here in enumerate(circles):
        there = circles[(index + 1) % len(circles)]
        dx = there['center'][0] - here['center'][0]
        dy = there['center'][1] - here['center'][1]
        distance = math.hypot(dx, dy)
        delta = (sense(here) * here['radius']
                 - sense(there) * there['radius']) / distance
        sideways = math.sqrt(1.0 - delta * delta)
        result.append((delta * dx / distance - sideways * dy / distance,
                       delta * dy / distance + sideways * dx / distance))
    return result

def old_spans(circles, normals):
    result = []
    for index, normal in enumerate(normals):
        following = (index + 1) % len(circles)
        def touch(circle):
            reach = sense(circle) * circle['radius']
            return (circle['center'][0] + reach * normal[0],
                    circle['center'][1] + reach * normal[1])
        start, end = touch(circles[index]), touch(circles[following])
        result.append((start, (normal[1], -normal[0]), math.dist(start, end)))
    return result

def old_arcs(circles, normals):
    result = []
    for index in range(len(circles)):
        following = (index + 1) % len(circles)
        onward = sense(circles[following])
        arrival = math.atan2(onward * normals[index][1],
                             onward * normals[index][0])
        departure = math.atan2(onward * normals[following][1],
                               onward * normals[following][0])
        turn = (onward * (arrival - departure)) % (2 * math.pi)
        result.append(circles[following]['radius'] * turn)
    return result

cases = {
    'actual': belt_circles(),
    'outer_unequal': [{'center': (1.25, -2.5), 'radius': 3.5},
                      {'center': (19.0, 8.0), 'radius': 7.25}],
    'back_idler': [{'center': (0.0, 0.0), 'radius': 4.0},
                   {'center': (14.0, 3.0), 'radius': 2.0,
                    'turn': 'counterclockwise'}],
    'zero_first': [{'center': (0.0, 0.0), 'radius': 0.0},
                   {'center': (6.0, 8.0), 'radius': 2.0}],
    'both_zero': [{'center': (0.0, 0.0), 'radius': 0.0},
                  {'center': (6.0, 8.0), 'radius': 0.0}],
    'zero_span_limit': [{'center': (0.0, 0.0), 'radius': 2.0},
                        {'center': (5.0, 0.0), 'radius': 3.0,
                         'turn': 'counterclockwise'}],
}
def flat(value):
    if isinstance(value, (tuple, list)):
        for item in value:
            yield from flat(item)
    else:
        yield float(value)
for name, circles in cases.items():
    old_n, new_n = old_normals(circles), gt2._normals(circles)
    old_s, new_s = old_spans(circles, old_n), gt2.spans(circles)
    old_a, new_a = old_arcs(circles, old_n), gt2._arcs(circles)
    difference = lambda a, b: max(abs(x-y) for x, y in zip(flat(a), flat(b)))
    print(name, difference(old_n, new_n), difference(old_s, new_s),
          difference(old_a, new_a), gt2.stations(circles), gt2.length(circles))
PY
/home/asa/devel/machinome-studio/.venv/bin/python - <<'PY'
import math, re
from solid2 import get_animation_time
from machinome.core.expressions import parse, render
from machinome_mechanics import belt_tangent_points

def evaluate(expression, sample):
    source = render(parse(str(expression))).replace('$t', repr(sample))
    source = re.sub(r'\bsqrt\(', 'SQRT(', source)
    return eval(source, {'__builtins__': {}}, {'SQRT': math.sqrt})

t = get_animation_time()
points = belt_tangent_points((t, 2*t), 2+t/10, (20-t, 7), 3, 1, -1)
print(tuple(tuple(str(value) for value in point) for point in points))
for sample in (-1, 0, .25, 1, 2):
    print(sample, tuple(tuple(evaluate(value, sample) for value in point)
                        for point in points))
PY
/home/asa/devel/machinome-studio/.venv/bin/machinome test --faceted simulation/winch.py:WinchABC
/home/asa/devel/machinome-studio/.venv/bin/machinome test --faceted simulation/hangprinter.py
/home/asa/devel/machinome-studio/.venv/bin/machinome test --exact simulation/winch.py:WinchABC
/home/asa/devel/machinome-studio/.venv/bin/machinome test --exact simulation/hangprinter.py
/home/asa/devel/machinome-studio/.venv/bin/machinome build
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot simulation/winch.py:WinchABC -o /tmp/hangprinter-belt-tangents-winch.png --autocenter --viewall
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot -o /tmp/hangprinter-belt-tangents-rest.png --autocenter
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot -o /tmp/hangprinter-belt-tangents-lift.png --autocenter --drive z=300
```

Before the edit the actual winch loop measured 605.3484495084118 mm, with
span lengths 40.73058794215619, 33.09260933528969, and
107.20218786644189 mm and arc lengths 8.22905219600879,
18.566088856693735, and 397.5279233118215 mm.  Its faceted winch suite passed
5/5.  After the edit the independent old/new probe found maximum normal and
span-component differences of `8.62e-16` and `5.68e-14` on that loop and a
maximum arc difference of `5.68e-14` mm.  Back-idler arc lengths remained
8.012816409461738 and 16.025632818923476 mm exactly.  Both-zero-radius and
limiting zero-span routes retained zero arcs; the limiting route retained zero
length and all-zero stations, so floating regrouping did not turn a zero wrap
into a full revolution.  The other representative cases differed by no more
than `1.78e-15` in any span component.

The raw deferred helper probe used `solid2.get_animation_time()` in both
centres and one radius.  Its four contact coordinates serialized as deferred
OpenSCAD expressions and evaluated successfully at all five samples.  The
first attempt to reuse the mechanics repository's private test evaluator
failed with `ModuleNotFoundError: tests.test_mechanisms`; the recorded result
above came from a self-contained evaluator using the framework expression
parser.  Hangprinter's wrapper remains intentionally numeric rather than
claiming a new symbolic project interface.

Post-edit faceted and exact suites each passed 5/5 for the winch and 19/19 for
the root.  The build succeeded (`Published artifacts are already current`).
The focused winch image shows the belt still leaving the spool gear, reversing
over the small idler, and reaching the motor gear on the recorded route.  The
rest and `z=300` overview images show the expected whole-machine poses and
line endpoints.  These pixels and contracts cover only modeled geometry and
motion; they do not certify force, tension, elasticity, or physical contact.

The mechanics worktree base planning commit was
`38fa3bf6d084738ca7c75534a36d0fd1a6dc88e0`; it did not contain the tested
implementation.  The uncommitted `machinome_mechanics/belts.py` code identity
was SHA-256
`28e693a5b2b213526c6f235615306fbad0a47f0ad0fca579d2aa1142f5db8cab`.
Framework HEAD remained `0ce71cdea6cc4a2e7fd7e85dc68847daef3d34cc` and
viewer HEAD remained `4355da1a7f64dacd7d86eb27dbdfdf7ced94598f`; both
dependency worktrees were clean before and after these checks.  This project
tested those live dependency heads through the explicit overlay; it does not
claim a pinned environment.
