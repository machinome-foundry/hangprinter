"""The ceiling unit: `full_winch()`, in its own frame -- Z up off the
plate -- with its four winches at their stations, their brackets and
line guides, the three verticalizers and four horizontal deflectors the
D and A lines leave through, the wire rewinder, the landing brackets,
the ODrives and the plate.  The machine hangs it under anchor D upside
down.

The ceiling knows which way each winch's line leaves its spool --
`spool_sense()` signs a stack turn for it -- but no longer carries any
line's millimetres itself: the root binds each winch's stack coordinate
directly, by path, once it has converted a line length to a turn.
"""

import math

import numpy
from solid2 import circle, cylinder, linear_extrude, square
from machinome.node import AssemblyNode, Solid2Node
from machinome.parameters import Length

from simulation import layout, materials
from simulation.frames import chain
from simulation.layout import (
    A, B, C, D,
    BRACKET,
    DEFLECTOR_A, DEFLECTOR_B, DEFLECTOR_C,
    LANDING_BRACKETS,
    ODRIVE_HOLE_DIAMETER, ODRIVE_HOLES, ODRIVE_SIZE, ODRIVES,
    PLATE, PLATE_SIZE,
    WINCH_STATIONS,
    WIRE_REWINDER,
    Cc_plastic_length,
)
from simulation.part import MIRROR_Y, Box, DesignStl, ScadPart, place
from simulation.scad import landing_brackets
from simulation.winch import WinchABC, WinchD


class MotorBracketA(DesignStl):
    stl_source = '../stl/motor_bracket_A.stl'


class MotorBracketB(DesignStl):
    stl_source = '../stl/motor_bracket_B.stl'


class MotorBracketC(DesignStl):
    stl_source = '../stl/motor_bracket_C.stl'


class MotorBracketD(DesignStl):
    stl_source = '../stl/motor_bracket_D.stl'


class TiltedDeflector(DesignStl):
    """`new_tilted_line_deflector.stl` is a print pack: the holder and
    its two bearing sticks laid out beside it.  The layout imports the
    pack whole; the holder is the part, and the sticks, for which the
    design states no assembled position, are left out.  Winch B's is
    the layout's `mirror([0, 1, 0])`."""
    stl_source = '../stl/new_tilted_line_deflector.stl'
    body = 0
    MIRROR_AXIS = MIRROR_Y


class Verticalizer(DesignStl):
    stl_source = '../stl/line_verticalizer.stl'


class HorizontalDeflector(DesignStl):
    stl_source = '../stl/horizontal_line_deflector.stl'


class WireRewinder(DesignStl):
    stl_source = '../stl/line_roller_wire_rewinder.stl'


class LandingBracketA(ScadPart):
    def render(self):
        return landing_brackets.landing_bracket_a()


class LandingBracketB(ScadPart):
    def render(self):
        return landing_brackets.landing_bracket_b()


class LandingBracketC(ScadPart):
    def render(self):
        return landing_brackets.landing_bracket_c()


class Plate(Box):
    color = materials.PLATE


class ODrive(Solid2Node):
    """The layout's `odrive()`: a 140 x 50 board, 2 thick, with a 3 mm
    hole in each corner.  The layout also cuts the word "ODrive" through
    it; a cut letter's counters would be loose bodies, so the word is
    not cut here."""

    color = materials.ODRIVE
    fn = 24

    def render(self):
        board = square([ODRIVE_SIZE[0], ODRIVE_SIZE[1]])
        for x, y in ODRIVE_HOLES:
            board -= circle(d=ODRIVE_HOLE_DIAMETER).translate([x, y])
        return linear_extrude(height=ODRIVE_SIZE[2])(board)


class Ceiling(AssemblyNode):

    beam_length = Length(layout.Beam_length, min=0)
    sidelength = beam_length + Length(2 * Cc_plastic_length)

    winch_a = WinchABC(left_handed=True)
    winch_b = WinchABC(left_handed=True)
    winch_c = WinchABC()
    winch_d = WinchD()
    bracket_a = MotorBracketA()
    bracket_b = MotorBracketB()
    bracket_c = MotorBracketC()
    bracket_d = MotorBracketD()
    deflector_a = TiltedDeflector()
    deflector_b = TiltedDeflector(mirrored=True)
    deflector_c = TiltedDeflector()
    verticalizers = Verticalizer().repeat(3)
    deflectors = HorizontalDeflector().repeat(4)
    rewinder = WireRewinder()
    landing_a = LandingBracketA()
    landing_b = LandingBracketB()
    landing_c = LandingBracketC()
    odrives = ODrive().repeat(2)
    plate = Plate(x=PLATE_SIZE[0], y=PLATE_SIZE[1], z=PLATE_SIZE[2])

    @property
    def winches(self):
        return {A: self.winch_a, B: self.winch_b, C: self.winch_c, D: self.winch_d}

    def spool_sense(self, index):
        """+1 when a positive turn about a winch's stack axis pays its
        line out along the segment that leaves its spool, else -1: the
        bottom of the spool, `Spool_r` under the axis, moves with
        `axis x down`.  Both directions are in the winch's own frame.
        Which way a winch's line leaves its spool is the ceiling's own
        knowledge -- it needs the sidelength and the winch's axis."""
        axis = self.winches[index].AXIS
        _, exit_direction = layout.spool_exit(index, self.sidelength)
        moving = numpy.cross(axis, (0.0, 0.0, -1.0))
        return 1.0 if float(numpy.dot(moving, exit_direction)) > 0 else -1.0

    def render(self):
        for index, winch in self.winches.items():
            place(winch, WINCH_STATIONS[index])
        for index, bracket in ((A, self.bracket_a), (B, self.bracket_b),
                               (C, self.bracket_c), (D, self.bracket_d)):
            place(bracket, chain(WINCH_STATIONS[index], BRACKET))
        place(self.deflector_a, chain(WINCH_STATIONS[A], DEFLECTOR_A))
        place(self.deflector_b, chain(WINCH_STATIONS[B], DEFLECTOR_B), MIRROR_Y)
        place(self.deflector_c, chain(WINCH_STATIONS[C], DEFLECTOR_C))
        for node, matrix in zip(self.verticalizers, layout.verticalizers(self.sidelength)):
            place(node, matrix)
        for node, matrix in zip(self.deflectors, layout.horizontal_deflectors(self.sidelength)):
            place(node, matrix)
        place(self.rewinder, WIRE_REWINDER)
        place(self.landing_a, LANDING_BRACKETS['a'])
        place(self.landing_b, LANDING_BRACKETS['b'])
        place(self.landing_c, LANDING_BRACKETS['c'])
        for node, matrix in zip(self.odrives, ODRIVES):
            place(node, matrix)
        place(self.plate, PLATE)
