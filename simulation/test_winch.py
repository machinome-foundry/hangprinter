"""Contracts one winch keeps on its own: the belt on its three circles
and clear of the parts around it, and the parts holding together.  What
turns is asked of the whole machine, which owns the drivers."""

import math

import numpy
from machinome.test import TestCase

from simulation.layout import (
    BELT_ROLLER_CENTRE, GT2_belt_width, GT2_motor_gear_teeth, GT2_spool_gear_teeth,
    MOTOR_SHAFT, b623_outer_dia, bearing_z)
from simulation.measure import interferences, radial_distances
from simulation.winch import WinchABC

#: The three axes the belt runs on, in the winch frame: all along Y.
SPOOL_AXIS = (numpy.array([0.0, 0.0, bearing_z]), numpy.array([0.0, 1.0, 0.0]))
ROLLER_AXIS = (numpy.array([BELT_ROLLER_CENTRE[0], 0.0, BELT_ROLLER_CENTRE[1]]),
               numpy.array([0.0, 1.0, 0.0]))
MOTOR_AXIS = (numpy.array(MOTOR_SHAFT), numpy.array([0.0, 1.0, 0.0]))

#: The pitch radii, by the test's own arithmetic: teeth times pitch
#: around, and the tooth's reach inside the pitch line.
SPOOL_PITCH = GT2_spool_gear_teeth * 2.0 / (2 * math.pi)
MOTOR_PITCH = GT2_motor_gear_teeth * 2.0 / (2 * math.pi)
TOOTH_REACH = 0.254 + 0.75
BACK = 1.38 - TOOTH_REACH

#: What the belt's back may share with the spool cover's rim rail, which
#: the design leaves in the belt's path where it leaves the gear: 0.06
#: mm deep on the model.  A finding, recorded in the design; not a
#: clearance the drawing states.
COVER_RAIL_ALLOWANCE = 0.25


class WinchTest(TestCase):

    node = WinchABC

    def belt_vertices(self):
        return self.node.belt.mesh.vertices

    def test_the_belt_rides_its_three_circles(self):
        vertices = self.belt_vertices()
        # the spool gear: crests on the flank circle, the back a belt out,
        # over most of the way round
        radii, _ = radial_distances(vertices, *SPOOL_AXIS)
        self.assertAlmostEqual(radii.min(), SPOOL_PITCH - TOOTH_REACH, delta=0.1)
        back = numpy.abs(radii - (SPOOL_PITCH + BACK)) < 0.1
        # the arc is one of the loop's six elements, half its vertices on the back
        self.assertGreater(back.sum(), len(vertices) / 12 * 0.75)
        # the motor gear likewise
        radii, _ = radial_distances(vertices, *MOTOR_AXIS)
        self.assertAlmostEqual(radii.min(), MOTOR_PITCH - TOOTH_REACH, delta=0.1)
        # the roller: the belt's back on the bearing
        radii, _ = radial_distances(vertices, *ROLLER_AXIS)
        self.assertAlmostEqual(radii.min(), b623_outer_dia / 2, delta=0.1)
        # and the belt is centred on the spool gear's width
        self.assertAlmostEqual(vertices[:, 1].max(), GT2_belt_width / 2, delta=0.01)
        self.assertAlmostEqual(vertices[:, 1].min(), -GT2_belt_width / 2, delta=0.01)

    def test_the_belt_turns_on_the_roller_between_gear_and_motor(self):
        """The belt leaves the spool gear straight down, turns on the
        roller, and runs level onto the top of the motor gear."""
        vertices = self.belt_vertices()
        # a vertical run at the spool gear's side, outside the gear
        # (2 degrees off vertical: the roller's rim is placed at the gear's
        # outer diameter plus 1.4, the belt's back on the gear is 1.27 mm
        # inside that)
        side = vertices[(vertices[:, 2] > 60) & (vertices[:, 2] < 80) & (vertices[:, 0] > 0)]
        self.assertGreater(len(side), 10)
        top = side[side[:, 2] > 78]
        bottom = side[side[:, 2] < 62]
        self.assertAlmostEqual(top[:, 0].min(), SPOOL_PITCH - TOOTH_REACH, delta=0.3)
        self.assertAlmostEqual(top[:, 0].max(), SPOOL_PITCH + BACK, delta=0.3)
        tilt = math.degrees(math.atan2(bottom[:, 0].mean() - top[:, 0].mean(),
                                       top[:, 2].mean() - bottom[:, 2].mean()))
        self.assertLess(abs(tilt), 3.0)
        # a level run between the roller and the motor, under the roller
        level = vertices[(vertices[:, 0] > BELT_ROLLER_CENTRE[0] + 8)
                         & (vertices[:, 0] < MOTOR_SHAFT[0] - 8)
                         & (vertices[:, 2] > 30)]
        self.assertGreater(len(level), 10)
        self.assertAlmostEqual(level[:, 2].max(), BELT_ROLLER_CENTRE[1] - b623_outer_dia / 2,
                               delta=0.2)

    def test_the_belt_clears_the_parts_around_it(self):
        belt = self.node.belt
        for part in (self.node.motor, self.node.encoder, self.node.rod):
            self.assertNotIntersecting(belt, part)
        for cover in (self.node.spool_cover, self.node.spool_cover_mirrored):
            self.assertIntersectVolumeBelow(belt, cover, COVER_RAIL_ALLOWANCE)

    def test_solid_integrity(self):
        self.assertNoDisconnectedSolids(self.node)

    def test_assembly_integrity(self):
        found = interferences(self.node)
        self.assertEqual(found, [], [f'{a.name} shares {v:.4f} mm³ with {b.name}' for a, b, v in found])
