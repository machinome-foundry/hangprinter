"""Contracts the machine has to keep.

Most of them are kept against the design itself: the layout's CSG
export says where every part and every line is, and the model is asked
to be there.  The rest are the machine's: the lines' lengths follow the
mover, the spools turn by what they pay out, the mover moves as one and
stays out of everything.
"""

import math

import numpy
from machinome.simulation import ScenarioTest
from machinome.test import TestCase

from simulation import csg, layout
from simulation.frames import apply
from simulation.hangprinter import Hangprinter
from simulation.layout import (
    A, B, C, D,
    ADVANTAGE, BED_TOP, CEILING, CEILING_LINES, MOVER_LIFT, WINCH_STATIONS, anchors,
    Spool_r, GT2_spool_gear_teeth, GT2_motor_gear_teeth, b623_outer_dia)
from simulation.measure import (
    design_file, interferences, moved, placement_error, printed_solids, profile_shift,
    radial_distances, same_segment, shared_volume, stl_nodes, strand_ends, strand_length, turned)
from simulation.part import MIRROR_X, MIRROR_Y
from simulation.winch import MOTOR_GEAR, MOTOR_GEAR_MIRRORED, BELT_ROLLERS, SANDWICH_ABC, SANDWICH_D

#: The poses the kinematic contracts are asked at.
ORIGIN = (0.0, 0.0, 0.0)
POSE = (300.0, -200.0, 450.0)
DESIGN_POSE = (100.0, -50.0, 200.0)

#: The design's expressions the Python constants restate.
DESIGN_NUMBERS = {
    'Sidelength': ('Sidelength', lambda: layout.sidelength()),
    'Cc_plastic_length': ('Cc_plastic_length', lambda: layout.Cc_plastic_length),
    'Cc_action_point_from_mid': ('Cc_action_point_from_mid', lambda: layout.Cc_action_point_from_mid),
    'cx': ('cx', lambda: layout.cx),
    'cy': ('cy', lambda: layout.cy),
    'bc_x_pos': ('bc_x_pos', lambda: layout.bc_x_pos),
    'lxm1': ('lxm1', lambda: layout.lxm1),
    'lx0': ('lx0', lambda: layout.lx0),
    'lx1': ('lx1', lambda: layout.lx1),
    'lx2': ('lx2', lambda: layout.lx2),
    'lx3': ('lx3', lambda: layout.lx3),
    'ly2': ('ly2', lambda: layout.ly2(layout.sidelength())),
    'spd': ('spd', lambda: layout.spd),
    'Sep_disc_radius': ('Sep_disc_radius', lambda: layout.Sep_disc_radius),
    'bearing_z': ('Sep_disc_radius + Gap_between_sandwich_and_plate', lambda: layout.bearing_z),
    'hz': ('Gap_between_sandwich_and_plate + Sep_disc_radius - Spool_r', lambda: layout.hz),
    'Sandwich_ABC_width': ('Sandwich_ABC_width', lambda: layout.Sandwich_ABC_width),
    'Sandwich_D_width': ('Sandwich_D_width', lambda: layout.Sandwich_D_width),
    'Smooth_rod_length_ABC': ('Smooth_rod_length_ABC', lambda: layout.Smooth_rod_length_ABC),
    'Smooth_rod_length_D': ('Smooth_rod_length_D', lambda: layout.Smooth_rod_length_D),
    'Belt_roller_bearing_xpos': ('Belt_roller_bearing_xpos', lambda: layout.Belt_roller_bearing_xpos),
    'Belt_roller_h': ('Belt_roller_h', lambda: layout.Belt_roller_h),
    'Torx_depth': ('Torx_depth', lambda: layout.Torx_depth),
    'Spool_cover_tot_height': ('Spool_cover_tot_height', lambda: layout.Spool_cover_tot_height),
    'Line_roller_ABC_winch_h': ('Line_roller_ABC_winch_h', lambda: layout.Line_roller_ABC_winch_h),
    'Corner_clamp_bearings_center_to_center': ('Corner_clamp_bearings_center_to_center',
                                               lambda: layout.Corner_clamp_bearings_center_to_center),
    'b623_big_ugroove_small_r': ('b623_big_ugroove_small_r', lambda: layout.b623_big_ugroove_small_r),
    'Yshift_top_plate': ('Yshift_top_plate', lambda: layout.Yshift_top_plate),
    'anchor_A_y': ('anchors[0][1]', lambda: layout.anchors[A][1]),
    'anchor_D_z': ('anchors[3][2]', lambda: layout.anchors[D][2]),
}


def wrap(degrees):
    """An angle as `turned` reads it, in (-180, 180]."""
    return (degrees + 180.0) % 360.0 - 180.0


def rotate2(point, degrees):
    a = math.radians(degrees)
    x, y = point[0], point[1]
    return numpy.array([x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), point[2]])


#: What two parts may share by the design's own drawing, in mm³: each a
#: finding recorded in the design, none a clearance the drawing states.
#: A pair is (name of one, name of the other); order does not matter.
ALLOWED = {
    ('encoder', 'bracket_a'): 2.1,       # the render motor's encoder board sits in the bracket
    ('encoder', 'bracket_b'): 2.1,
    ('encoder', 'bracket_c'): 2.1,
    ('encoder', 'bracket_d'): 2.1,
    ('dright_spool_top', 'dright_spool_bottom'): 5.3,   # the D spool's halves, 9 mm apart as placed
    ('extruder', 'holder'): 7.5,         # a 40-gon tube in a 60-gon ring of the same diameter
    ('extruder', 'top_holder'): 0.01,
    ('beams', 'clamps'): 0.1,            # the beam's end corners in the clamp's rounded pocket
    ('towers', 'bullets'): 131.0,        # the design's bullet() seats the bullet 1 mm into the sleeve's back wall
}


def allowed(a, b):
    """The allowance for the pair, or 0."""
    names = (a.name.split('-')[0], b.name.split('-')[0])
    return ALLOWED.get(names, ALLOWED.get(names[::-1], 0.0))


def excess(found):
    """The pairs sharing more than the design's own overlap."""
    return [(a, b, v) for a, b, v in found if v > allowed(a, b)]


class HangprinterTest(TestCase):

    node = Hangprinter

    def setUp(self):
        self.node.set_state(x=0.0, y=0.0, z=0.0)

    # -- the design's numbers -------------------------------------------------------

    def test_the_constants_are_the_designs(self):
        values = csg.echo({name: expr for name, (expr, _) in DESIGN_NUMBERS.items()})
        for name, (_, ours) in DESIGN_NUMBERS.items():
            self.assertIn(name, values)
            self.assertAlmostEqual(ours(), values[name], delta=0.001, msg=name)

    # -- ceiling-unit-layout, mover-assembly, anchor-station: parity --------------------

    def design_leaves(self, position=ORIGIN):
        return [leaf for leaf in csg.leaves(position) if not leaf.subtracted]

    def test_every_import_stands_where_the_design_puts_it(self):
        imports = [leaf for leaf in self.design_leaves() if leaf.kind == 'import']
        matched = set()
        for node in stl_nodes(self.node):
            file = design_file(node)
            candidates = [(index, leaf) for index, leaf in enumerate(imports) if leaf.file == file]
            self.assertTrue(candidates, f'{node.name}: the design never imports {file}')
            errors = []
            for index, leaf in candidates:
                mirrored = numpy.linalg.det(leaf.matrix[:3, :3]) < 0
                if mirrored != bool(getattr(node, 'mirrored', False)):
                    continue
                axis = node.MIRROR_AXIS if mirrored else None
                errors.append((placement_error(node, leaf.matrix, axis), index))
            self.assertTrue(errors, f'{node.name}: no import of {file} with its handedness')
            error, index = min(errors)
            self.assertLess(error, 0.01, f'{node.name} stands {error:.3f} mm off the design')
            matched.add(index)
        unmatched = [imports[i] for i in range(len(imports)) if i not in matched]
        self.assertEqual(unmatched, [], f'the design places these and the model does not: {unmatched}')

    def _match_bounds(self, node, leaves, what):
        bounds = node.mesh.bounds
        error = min(float(numpy.abs(leaf.cube_bounds() - bounds).max()) for leaf in leaves)
        self.assertLess(error, 0.01, f'{node.name} ({what}) stands {error:.3f} mm off the design')

    def _match_centre(self, node, leaves, what, extent):
        """A squat part against the design's cylinder: same centre, and
        the same extent along the cylinder's axis."""
        bounds = node.mesh.bounds
        centre = bounds.mean(axis=0)
        error = numpy.inf
        for leaf in leaves:
            a, b = leaf.cylinder_ends()
            axis = (b - a) / numpy.linalg.norm(b - a)
            along = (node.mesh.vertices - a) @ axis
            error = min(error, max(numpy.linalg.norm(centre - (a + b) / 2),
                                   abs(along.min()), abs(along.max() - extent)))
        self.assertLess(error, 0.02, f'{node.name} ({what}) stands {error:.3f} mm off the design')

    def _match_ends(self, node, leaves, what):
        ends = strand_ends(node)
        error = min(min(numpy.linalg.norm(ends[0] - a) + numpy.linalg.norm(ends[1] - b),
                        numpy.linalg.norm(ends[0] - b) + numpy.linalg.norm(ends[1] - a))
                    for a, b in (leaf.cylinder_ends() for leaf in leaves))
        self.assertLess(error, 0.02, f'{node.name} ({what}) stands {error:.3f} mm off the design')

    def test_primitives_stand_where_the_design_puts_them(self):
        leaves = self.design_leaves()
        cubes = [leaf for leaf in leaves if leaf.kind == 'cube']
        cylinders = [leaf for leaf in leaves if leaf.kind == 'cylinder']

        def cubes_of(size):
            return [leaf for leaf in cubes if numpy.allclose(leaf.params['size'], size, atol=0.01)]

        def cylinders_of(radius, height):
            return [leaf for leaf in cylinders
                    if abs(leaf.params['r1'] - radius) < 0.01 and abs(leaf.params['h'] - height) < 0.01]

        mover = self.node.mover
        for beam in mover.beams:
            self._match_bounds(beam, cubes_of([400, 15, 15]), 'beam')
        self._match_bounds(self.node.ceiling.plate, cubes_of(layout.PLATE_SIZE), 'plate')
        self._match_bounds(self.node.bed, cubes_of(layout.BED_SIZE), 'bed')
        for anchor in self.node.anchors:
            self._match_bounds(anchor.plate, cubes_of(layout.ANCHOR_PLATE_SIZE), 'anchor plate')
        for clip in mover.marker_clips:
            self._match_bounds(clip, cubes_of([10, 20, 20]), 'marker clip')
        for marker in mover.markers:
            vertices = marker.mesh.vertices
            centre = vertices.mean(axis=0)
            rim = vertices[numpy.hypot(vertices[:, 0] - centre[0], vertices[:, 1] - centre[1]) > 44]
            error = min(max(abs(rim[:, 2].min() - min(a[2], b[2])), abs(rim[:, 2].max() - max(a[2], b[2])),
                            numpy.linalg.norm(rim.mean(axis=0)[:2] - a[:2]))
                        for a, b in (leaf.cylinder_ends() for leaf in cylinders_of(45, 1)))
            self.assertLess(error, 0.02, f'{marker.name} stands {error:.3f} mm off the design')
        for winch in self.node.ceiling.winches.values():
            self._match_ends(winch.rod, cylinders_of(4, winch.rod.length), 'smooth rod')
            for roller in winch.rollers:
                self._match_centre(roller, cylinders_of(5, 4), 'belt roller', 4.0)

    def test_module_parts_stand_where_the_design_puts_them(self):
        """Parts drawn from the design's modules, against the primitives
        the design draws them with."""
        mover = self.node.mover
        holder = mover.holder.mesh.bounds
        self.assertAlmostEqual(holder[0][2], -287.0, delta=0.01)
        self.assertAlmostEqual(holder[1][2], -277.0, delta=0.01)
        self.assertLess(abs(holder.mean(axis=0)[0]), 0.05)      # symmetric about X
        top = mover.top_holder.mesh.bounds
        self.assertAlmostEqual(top[0][2], 399.0, delta=0.01)
        self.assertAlmostEqual(top[1][2], 409.0, delta=0.01)
        plate_bottom = apply(CEILING, (0, 0, 0))[2]
        # the landing brackets: on the plate, and as deep as the design's
        # gaping-mouth cubes reach
        mouths = [leaf for leaf in self.design_leaves()
                  if leaf.kind == 'cube' and abs(leaf.params['size'][2] - 60) < 0.01]
        deepest = min(leaf.cube_bounds()[0][2] for leaf in mouths)
        brackets = (self.node.ceiling.landing_a, self.node.ceiling.landing_b,
                    self.node.ceiling.landing_c)
        for bracket in brackets:
            self.assertAlmostEqual(bracket.mesh.bounds[1][2], plate_bottom, delta=0.01)
        self.assertAlmostEqual(min(b.mesh.bounds[0][2] for b in brackets), deepest, delta=0.05)
        for odrive in self.node.ceiling.odrives:
            bounds = odrive.mesh.bounds
            self.assertAlmostEqual(bounds[1][2], plate_bottom, delta=0.01)
            self.assertAlmostEqual(bounds[0][2], plate_bottom - 2.0, delta=0.01)

    def test_the_nozzle_hangs_where_the_design_puts_it(self):
        """The clay extruder's nozzle stands one millimetre over the bed
        with the mover at the origin: the layout lowered the anchors by
        the extruder's 350 mm for exactly that."""
        tip = self.node.mover.nozzle.mesh.bounds[0][2]
        self.assertAlmostEqual(tip, BED_TOP + 1.0, delta=0.01)
        self.assertAlmostEqual(tip, -349.0, delta=0.01)

    def test_the_alternative_toolhead(self):
        machine = Hangprinter(clay=False)
        machine.set_state(x=0.0, y=0.0, z=0.0)
        machine.assemble()
        machine.build_stls()
        mover = machine.mover
        names = [child.name for child in mover.children]
        for absent in ('extruder', 'nozzle', 'holder', 'top_holder'):
            self.assertNotIn(absent, names)
        for present in ('short_beam', 'extruder_holder', 'hotend', 'drive_box'):
            self.assertIn(present, names)
        self.assertAlmostEqual(mover.hotend.mesh.bounds[0][2], 0.0, delta=0.01)
        self.assertEqual(excess(interferences(mover)), [])

    # -- line-path -------------------------------------------------------------------

    def strands(self):
        return (list(self.node.internal) + list(self.node.d_lines) + list(self.node.anchor_lines))

    def test_the_strands_match_the_designs_lines(self):
        for pose in (ORIGIN, DESIGN_POSE):
            self.node.set_state(x=pose[0], y=pose[1], z=pose[2])
            lines = [leaf for leaf in self.design_leaves(pose)
                     if leaf.kind == 'cylinder' and abs(leaf.params['r1'] - 1.0) < 1e-9
                     and leaf.params['h'] > 30]
            self.assertEqual(len(lines), 34)
            ends = [strand_ends(strand) for strand in self.strands()]
            for leaf in lines:
                a, b = leaf.cylinder_ends()
                self.assertTrue(any(same_segment(e, a, b, 0.05) for e in ends),
                                f'no strand for the design line {a.round(2)} -> {b.round(2)} at {pose}')

    def test_a_pose_moves_only_the_mover_end(self):
        self.node.set_state(x=0.0, y=0.0, z=0.0)
        rest = [strand_ends(s) for s in list(self.node.d_lines) + list(self.node.anchor_lines)]
        self.node.set_state(x=POSE[0], y=POSE[1], z=POSE[2])
        shift = numpy.array(POSE)
        for strand, (near0, far0) in zip(list(self.node.d_lines) + list(self.node.anchor_lines), rest):
            near, far = strand_ends(strand)
            self.assertLess(numpy.linalg.norm(near - near0), 0.01, strand.name)
            self.assertLess(numpy.linalg.norm(far - far0 - shift), 0.05, strand.name)

    def test_the_runs_join_the_stubs_to_the_anchors(self):
        stubs = layout.stubs(layout.sidelength())
        far_ends = [far for winch in (A, B, C) for far, _ in stubs[winch]]
        lows = {i: [anchors[i] + rotate2(p, i * 120) for p in layout.action_points(layout.sidelength())[1::2]]
                for i in (A, B, C)}
        plate = self.node.ceiling.plate.mesh.bounds
        for index, run in enumerate(self.node.runs):
            near, far = strand_ends(run)
            self.assertLess(min(numpy.linalg.norm(near - end) for end in far_ends), 0.05, run.name)
            anchor = (A, A, B, B, C, C)[index]
            self.assertLess(min(numpy.linalg.norm(far - low) for low in lows[anchor]), 0.05, run.name)
            # and it heads away from the plate once clear of its start
            for t in numpy.linspace(0.0, 1.0, 50):
                point = near + t * (far - near)
                if numpy.linalg.norm(point - near) < 60:
                    continue
                gap = numpy.maximum(0, numpy.maximum(plate[0] - point, point - plate[1]))
                self.assertGreater(numpy.linalg.norm(gap), 20, f'{run.name} passes the plate')

    # -- line-kinematics ---------------------------------------------------------------

    def expected_length(self, anchor, pose):
        pos = numpy.array(pose, dtype=float)
        lift = numpy.array(MOVER_LIFT) if anchor == D else 0.0
        return float(numpy.linalg.norm(anchors[anchor] - pos - lift))

    def test_line_lengths_follow_the_mover(self):
        for pose in (ORIGIN, POSE):
            self.node.set_state(x=pose[0], y=pose[1], z=pose[2])
            for strand in self.node.d_lines:
                self.assertAlmostEqual(strand_length(strand), self.expected_length(D, pose), delta=0.05)
            for index, strand in enumerate(self.node.anchor_lines):
                anchor = (A, B, C)[index // 4]
                self.assertAlmostEqual(strand_length(strand), self.expected_length(anchor, pose),
                                       delta=0.05, msg=strand.name)

    def test_the_mover_moves_as_one(self):
        self.node.set_state(x=0.0, y=0.0, z=0.0)
        parts = printed_solids(self.node.mover)
        before = {part: part.mesh.vertices.copy() for part in parts}
        self.node.set_state(x=POSE[0], y=POSE[1], z=POSE[2])
        for part in parts:
            common, spread = moved(part, before[part])
            self.assertLess(numpy.linalg.norm(common - POSE), 0.01, part.name)
            self.assertLess(spread, 0.01, part.name)

    # -- spool-drive -------------------------------------------------------------------

    def winch_axes(self, index):
        """The stack's axis, the motor gear's axis and the rollers' axes
        of winch `index`, in the machine frame, as (point, direction)."""
        station = CEILING @ WINCH_STATIONS[index]
        sandwich = SANDWICH_D if index == D else SANDWICH_ABC
        gear = MOTOR_GEAR_MIRRORED if index in (A, B) else MOTOR_GEAR
        return {
            'stack': (apply(station @ sandwich, (0, 0, 0)), (station @ sandwich)[:3, 2]),
            'gear': (apply(station @ gear, (0, 0, 0)), (station @ gear)[:3, 2]),
            'rollers': [(apply(station @ m, (0, 0, 0)), (station @ m)[:3, 2]) for m in BELT_ROLLERS],
        }

    def exit_sense(self, index, axis_point, axis_direction):
        """+1 when a positive turn about the stack's axis moves the line's
        tangent point along the segment that leaves the spool, by the
        test's own reading of the design's first internal line."""
        start, end = layout.internal_lines(layout.sidelength())[index][0]
        p0, p1 = apply(CEILING_LINES, start), apply(CEILING_LINES, end)
        exit_direction = (p1 - p0) / numpy.linalg.norm(p1 - p0)
        # the tangent point: on the axis's cross-section, toward the line
        tangent = p0 - axis_point
        tangent -= numpy.dot(tangent, axis_direction) * axis_direction
        tangent = tangent / numpy.linalg.norm(tangent) * Spool_r
        velocity = numpy.cross(axis_direction, tangent)
        return 1.0 if numpy.dot(velocity, exit_direction) > 0 else -1.0

    def test_the_stacks_turn_by_the_line_they_pay_out(self):
        self.node.set_state(x=0.0, y=0.0, z=0.0)
        winches = self.node.ceiling.winches
        parts = {}
        for index, winch in winches.items():
            parts[index] = [winch.rotor.spool_gear, winch.motor_gear] + list(winch.rollers)
        before = {part: part.mesh.vertices.copy() for index in parts for part in parts[index]}
        turning = [q for index in parts for q in parts[index]]
        turning += [leaf for w in winches.values() for leaf in printed_solids(w.rotor)]
        still = [p for p in printed_solids(self.node.ceiling) if not any(p is q for q in turning)]
        still_before = {part: part.mesh.vertices.copy() for part in still}

        self.node.set_state(x=POSE[0], y=POSE[1], z=POSE[2])
        ratio = GT2_spool_gear_teeth / GT2_motor_gear_teeth
        pitch_radius = GT2_spool_gear_teeth * 2.0 / (2 * math.pi)
        for index, winch in winches.items():
            axes = self.winch_axes(index)
            point, direction = axes['stack']
            sense = self.exit_sense(index, point, direction)
            paid = ADVANTAGE[index] * (self.expected_length(index, POSE) - self.expected_length(index, ORIGIN))
            expected = sense * math.degrees(paid / Spool_r)
            stack, gear, *rollers = parts[index]
            self.assertAlmostEqual(turned(stack, before[stack], point, direction), wrap(expected),
                                   delta=0.01, msg=f'winch {layout.WINCH_NAMES[index]} stack')
            self.assertAlmostEqual(turned(gear, before[gear], axes['gear'][0], direction),
                                   wrap(ratio * expected), delta=0.05,
                                   msg=f'winch {layout.WINCH_NAMES[index]} motor gear')
            for roller, (rpoint, _) in zip(rollers, axes['rollers']):
                self.assertAlmostEqual(turned(roller, before[roller], rpoint, direction),
                                       wrap(-expected * pitch_radius / (b623_outer_dia / 2)), delta=0.1,
                                       msg=f'winch {layout.WINCH_NAMES[index]} roller')
        for part in still:
            common, spread = moved(part, still_before[part])
            self.assertLess(numpy.linalg.norm(common) + spread, 0.001, f'{part.name} moved')

    def test_the_belt_travels_with_its_gear(self):
        """Half a tooth of spool turn on winch A moves the belt's tooth
        pattern on the gear's arc by half a pitch, the gear's way, and
        the belt's `travel` port carries the gear's pitch-line travel."""
        pitch_degrees = 360.0 / GT2_spool_gear_teeth
        pitch_radius = GT2_spool_gear_teeth * 2.0 / (2 * math.pi)
        turn = 5.5 * pitch_degrees
        # the pose along Y that pays winch A that much line: the test's own inverse
        paid = math.radians(turn) * Spool_r / ADVANTAGE[A]
        wanted = self.expected_length(A, ORIGIN) + paid
        lo, hi = 0.0, 100.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if self.expected_length(A, (0.0, mid, 0.0)) < wanted else (lo, mid)
        winch = self.node.ceiling.winch_a
        point, direction = self.winch_axes(A)['stack']
        sense = self.exit_sense(A, point, direction)

        self.node.set_state(x=0.0, y=0.0, z=0.0)
        angles0, radii0 = self._tooth_profile(winch.belt.mesh.vertices, point, direction)
        gear_before = winch.rotor.spool_gear.mesh.vertices.copy()
        self.node.set_state(x=0.0, y=lo, z=0.0)
        angles1, radii1 = self._tooth_profile(winch.belt.mesh.vertices, point, direction)
        turned_by = turned(winch.rotor.spool_gear, gear_before, point, direction)
        self.assertAlmostEqual(turned_by, sense * turn, delta=0.02)
        shift = profile_shift(angles0, radii0, angles1, radii1, pitch_degrees / 20, pitch_degrees)
        self.assertAlmostEqual(abs(shift), pitch_degrees / 2, delta=pitch_degrees / 8)
        self.assertEqual(numpy.sign(shift), numpy.sign(turned_by))
        self.assertAlmostEqual(abs(winch.belt.travel.value), math.radians(turn) * pitch_radius, delta=0.01)

    def _tooth_profile(self, vertices, axis_point, axis_direction):
        """The belt's inner-face radius against angle about the spool
        axis, right-handed about `axis_direction`, over the middle of
        the wrap."""
        pitch_radius = GT2_spool_gear_teeth * 2.0 / (2 * math.pi)
        radii, along = radial_distances(vertices, axis_point, axis_direction)
        on_gear = radii < pitch_radius + 0.05
        r = vertices[on_gear] - axis_point
        axis = numpy.asarray(axis_direction) / numpy.linalg.norm(axis_direction)
        u = numpy.cross(axis, [0.0, 0.0, 1.0])
        u /= numpy.linalg.norm(u)
        v = numpy.cross(axis, u)
        angles = numpy.degrees(numpy.arctan2(r @ v, r @ u))
        keep = (angles > -100) & (angles < 100)
        return angles[keep], radii[on_gear][keep]

    def test_the_teeth_ride_together(self):
        """Along a move, the belt's teeth stay put on both gears' teeth:
        the volume the belt shares with each gear does not change.
        Teeth sweeping through each other would swing it through two
        cycles per tooth of gear turn (33 mm³ on the motor gear when the
        belt's phase ran the wrong way), so the swing is held under a
        tenth of that."""
        SWING = 3.0
        steps = numpy.linspace(0.0, 2.0, 9)      # about one motor-gear tooth on winch D
        for index, winch in self.node.ceiling.winches.items():
            for gear in (winch.motor_gear, winch.rotor.spool_gear):
                volumes = []
                for z in steps:
                    self.node.set_state(x=0.0, y=0.0, z=float(z))
                    volumes.append(shared_volume(winch.belt, gear))
                swing = max(volumes) - min(volumes)
                self.assertLess(swing, SWING,
                                f'winch {layout.WINCH_NAMES[index]} {gear.name}: shared volume swings '
                                f'{swing:.2f} mm³ along the move: {[round(v, 2) for v in volumes]}')

    def test_the_sense_pays_out(self):
        """Lengthening anchor A's line turns winch A so that the spool's
        tangent point moves along the line's exit."""
        self.node.set_state(x=0.0, y=0.0, z=0.0)
        stack = self.node.ceiling.winch_a.rotor.spool_gear
        before = stack.mesh.vertices.copy()
        self.node.set_state(x=0.0, y=100.0, z=0.0)          # anchor A is toward -Y: the line grows
        point, direction = self.winch_axes(A)['stack']
        turn = turned(stack, before, point, direction)
        self.assertGreater(abs(turn), 1.0)
        self.assertEqual(numpy.sign(turn), self.exit_sense(A, point, direction))

    # -- the whole machine ---------------------------------------------------------

    def test_solid_integrity(self):
        self.assertNoDisconnectedSolids(self.node)

    def test_assembly_integrity(self):
        """No two printed solids share volume, at the origin and at every
        instruction's target.  Decided on the engine (see `measure`)."""
        targets = [ORIGIN] + [
            tuple(instruction.targets.get(axis, 0.0) for axis in 'xyz')
            for instruction in self.node.instructions.values()]
        for pose in targets:
            self.node.set_state(x=pose[0], y=pose[1], z=pose[2])
            found = excess(interferences(self.node))
            self.assertEqual(found, [],
                             [f'{a.name} shares {v:.4f} mm³ with {b.name} at {pose}' for a, b, v in found])
            lowest = min(part.mesh.bounds[0][2] for part in printed_solids(self.node.mover))
            self.assertGreater(lowest, BED_TOP, f'the mover is in the bed at {pose}')
            highest = max(part.mesh.bounds[1][2] for part in printed_solids(self.node.mover))
            self.assertLess(highest, self.node.ceiling.plate.mesh.bounds[0][2],
                            f'the mover is in the ceiling at {pose}')


class HangprinterScenarioTest(ScenarioTest):
    """The machine driven through every instruction."""

    node = Hangprinter
    dt = 0.5
    meshes = True

    def check_clear(self):
        found = excess(interferences(self.node, among=printed_solids(self.node.mover)))
        assert found == [], [f'{a.name} shares {v:.4f} mm³ with {b.name}' for a, b, v in found]

    def test_homing_one_coordinate_holds_the_others(self):
        """From a pose reached by AnchorB and Lift, HomeX zeroes x alone."""
        sim = self.simulation()
        sim.at(0.0).trigger('AnchorB')
        sim.at(3.5).trigger('Lift')
        sim.at(8.0).trigger('HomeX')
        sim.run(11.0)
        target = self.node.instructions['AnchorB'].targets
        self.assertAlmostEqual(sim.state['x'], 0.0, delta=0.01)
        self.assertAlmostEqual(sim.state['y'], target['y'], delta=0.01)
        self.assertAlmostEqual(sim.state['z'], 900.0, delta=0.01)

    def test_the_instructions_move_the_mover_without_collision(self):
        sim = self.simulation()
        at = 0.0
        for name, hold in (('Lift', 4.5), ('AnchorA', 3.5), ('AnchorB', 3.5), ('AnchorC', 3.5),
                           ('Center', 3.5), ('HomeZ', 3.5), ('HomeX', 2.5), ('HomeY', 2.5)):
            sim.at(at).trigger(name)
            at += hold
        sim.every(1.0, self.check_clear)
        sim.run(at)
        for axis in 'xyz':
            self.assertAlmostEqual(sim.state[axis], 0.0, delta=0.01)
