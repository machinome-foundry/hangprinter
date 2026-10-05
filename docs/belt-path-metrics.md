# Belt path-metrics migration evidence

Hangprinter's GT2 wrappers now adapt their circle records once through
`machinome_mechanics.belt_path_metrics`.  `spans`, `stations`, and `length`
retain their public list/scalar forms.  The helper's circle-indexed arc lengths
rotate by one entry in `_arcs`, preserving this module's established
arc-after-span ordering.  Turn markers, fitted pitch, tooth count and phase,
controls, and surface allowances did not change.  The prior private normal and
tangent implementations were removed rather than retained as duplicate
production mechanics.

The clean base was `version_4` at
`12f74a6f00f0275cd2f289c703b0d122cc1875a9`.  Commands ran from the project
root with:

```sh
export PYTHONPATH="$PWD:/home/asa/devel/machinome-studio/WTs/mechanics-belt-path-metrics"
```

and the workspace Python and `machinome` executables.  This is the complete
independent legacy/new probe; it remains runnable without private production
helpers:

```sh
/home/asa/devel/machinome-studio/.venv/bin/python - <<'PY'
import math
from simulation import gt2
from simulation.winch import belt_circles

def sense(circle):
    return -1.0 if circle.get('turn') == 'counterclockwise' else 1.0


def legacy(circles):
    normals, spans = [], []
    for index, here in enumerate(circles):
        there = circles[(index + 1) % len(circles)]
        dx = there['center'][0] - here['center'][0]
        dy = there['center'][1] - here['center'][1]
        distance = math.hypot(dx, dy)
        delta = (sense(here) * here['radius']
                 - sense(there) * there['radius']) / distance
        sideways = math.sqrt(1.0 - delta * delta)
        normal = (delta * dx / distance - sideways * dy / distance,
                  delta * dy / distance + sideways * dx / distance)
        normals.append(normal)
        start = tuple(here['center'][axis]
                      + sense(here) * here['radius'] * normal[axis]
                      for axis in (0, 1))
        end = tuple(there['center'][axis]
                    + sense(there) * there['radius'] * normal[axis]
                    for axis in (0, 1))
        spans.append((start, (normal[1], -normal[0]), math.dist(start, end)))
    arcs = []
    for index in range(len(circles)):
        following = (index + 1) % len(circles)
        onward = sense(circles[following])
        arrival = math.atan2(onward * normals[index][1],
                             onward * normals[index][0])
        departure = math.atan2(onward * normals[following][1],
                               onward * normals[following][0])
        turn = (onward * (arrival - departure)) % (2 * math.pi)
        arcs.append(circles[following]['radius'] * turn)
    stations, at = [], 0.0
    for span, arc in zip(spans, arcs):
        stations.extend((at, at + span[2]))
        at += span[2] + arc
    return spans, arcs, stations, at


def flat(value):
    if isinstance(value, (tuple, list)):
        for item in value:
            yield from flat(item)
    else:
        yield float(value)


def difference(old, new):
    old_values, new_values = tuple(flat(old)), tuple(flat(new))
    assert len(old_values) == len(new_values)
    return max((abs(a-b) for a, b in zip(old_values, new_values)), default=0.0)


cases = {
    'actual': belt_circles(),
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

for name, circles in cases.items():
    old_spans, old_arcs, old_stations, old_length = legacy(circles)
    new_spans = gt2.spans(circles)
    new_arcs = gt2._arcs(circles)
    new_stations = gt2.stations(circles)
    new_length = gt2.length(circles)
    span_delta = difference(old_spans, new_spans)
    arc_delta = difference(old_arcs, new_arcs)
    station_delta = difference(old_stations, new_stations)
    length_delta = abs(old_length-new_length)
    assert max(span_delta, arc_delta, station_delta, length_delta) <= 1e-12
    print(name,
          'span', span_delta,
          'arc', arc_delta,
          'station', station_delta,
          'length', length_delta,
          'values', new_arcs, new_stations, new_length)
PY
```

Before editing, the actual loop's spans were 40.73058794215618,
33.09260933528969, and 107.20218786644189 mm; its after-span arcs were
8.229052196008796, 18.56608885669375, and 397.52792331182144 mm; total
length was 605.3484495084117 mm.  Its faceted winch suite passed 5/5.

After editing, every representative route retained identical total length.
The actual loop's maximum span, arc, and station differences were respectively
`2.13e-14`, `5.68e-14`, and `2.84e-14` mm.  The back-idler arc values remained
8.012816409461738 and 16.025632818923476 mm exactly.  One-zero-radius and
both-zero-radius cases retained their route lengths; the limiting inner
tangent retained zero spans, arcs, stations, and total length.  Thus neither
the helper's degree-based wrap calculation nor its circle-indexed fields
introduced a seam/full-revolution or ordering change.  The runnable probe
asserts equal flattened field cardinality and a `1e-12` absolute tolerance.

Validation commands and results were:

```sh
/home/asa/devel/machinome-studio/.venv/bin/machinome test --mesh simulation/winch.py:WinchABC
/home/asa/devel/machinome-studio/.venv/bin/machinome test --mesh simulation/hangprinter.py
/home/asa/devel/machinome-studio/.venv/bin/machinome test --brep simulation/winch.py:WinchABC
/home/asa/devel/machinome-studio/.venv/bin/machinome test --brep simulation/hangprinter.py
/home/asa/devel/machinome-studio/.venv/bin/machinome build
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot simulation/winch.py:WinchABC -o /tmp/hangprinter-belt-path-metrics-winch.png --autocenter --viewall
/home/asa/devel/machinome-studio/.venv/bin/machinome snapshot -o /tmp/hangprinter-belt-path-metrics-lift.png --autocenter --drive z=300
```

Faceted and exact suites each passed 5/5 for the winch and 19/19 for the root;
the build reported its published artifacts current.  Visual inspection of the
focused image found the belt still following the spool, back idler, and motor
gear route.  The driven overview showed the mover raised to `z=300`, with the
line endpoints and ceiling unit in their expected poses.  The images and
contracts cover modeled geometry and motion only; they do not certify force,
tension, elasticity, or physical contact.

Those two inspected images were generated against the earlier helper source
identity SHA-256
`8e7dc4203f44a62569f2de3062bdc89e6e93d2c206c50b6249ac659cd72e372f`.
After independent package review corrected an exact-360-degree seam without
changing the formula or adding a deadband, the asserting legacy probe, all four
faceted/exact project suites above, and the build were rerun against the final
helper source identity below.  The probe printed the same actual and
degenerate results, all suites again passed 5/5 and 19/19, and the build again
reported its artifacts current.  Because the Hangprinter route metrics were
numerically unchanged, the existing inspected images remain representative;
they are not presented as renders of the final helper hash.

The mechanics planning base was
`7c5193aa2446b36549804c847d24d3995ccbfa7b`; it did not contain the tested
implementation.  The uncommitted `machinome_mechanics/belts.py` code identity
was SHA-256
`09388c2cb4a3839f8c542c04cebfd5f29344dbee240023ccef7382171aa1a9dd`.
The earlier image/validation pass observed clean framework HEAD
`0ce71cdea6cc4a2e7fd7e85dc68847daef3d34cc` and viewer HEAD
`4355da1a7f64dacd7d86eb27dbdfdf7ced94598f`.  Before and after the final
corrected-helper probe, suites, and build, the viewer remained clean at that
head while framework main was clean at
`8d2bd71171be81f13ba5dd492851ed8b3a9ababb`; its concurrent ancestor-joint
constraint change did not alter this belt arithmetic.  This records the live
dependency states exercised through the explicit overlay, not a pinned
environment.
