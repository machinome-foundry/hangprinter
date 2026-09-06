"""The Hangprinter, as a machine.

Torbjørn's repository draws the printed parts and, in `layout.scad`, the
machine at rest for a figure; this package reads that figure into a
machine that moves.  The ceiling unit hangs under anchor D with its four
winches; the mover hangs from the lines; three anchors stand on the
floor.  The drivers are the mover's position -- `x`, `y`, `z` in the
design's frame, the calibrated origin on the bed -- and everything
follows: four line lengths, four spool angles, four motor gears, four
belts, and fifteen strands redrawn from the anchors and the ceiling to
the mover.
"""

import math

import numpy
from solid_node.math import sqrt
from solid_node.node import AssemblyNode
from solid_node.parameters import Flag, Length
from solid_node.simulation import Driver, Instruction

from simulation import layout
from simulation.anchor import Anchor
from simulation.ceiling import Ceiling
from simulation.frames import T, apply, chain
from simulation.layout import (
    A, B, C, D,
    ADVANTAGE,
    BED_CENTRE, BED_SIZE,
    CEILING, CEILING_LINES,
    Cc_plastic_length,
    MOVER_LIFT,
    anchors,
)
from simulation.mover import Mover
from simulation.part import Bed, MoverStrand, Strand, place

#: The travel the sliders offer: the bed, and the height under the ceiling.
REACH = 400.0
Z_MAX = 1200.0

#: Where the anchor instructions send the mover: toward each anchor's
#: azimuth, low over the bed.
ANCHOR_TARGET_RADIUS = 350.0
ANCHOR_TARGET_Z = 60.0


def _toward(anchor):
    azimuth = math.atan2(anchors[anchor][1], anchors[anchor][0])
    return {'x': ANCHOR_TARGET_RADIUS * math.cos(azimuth),
            'y': ANCHOR_TARGET_RADIUS * math.sin(azimuth),
            'z': ANCHOR_TARGET_Z}


class Hangprinter(AssemblyNode):

    #: The design's `Beam_length`: the mover's carbon beams.
    beam_length = Length(layout.Beam_length, min=0)
    #: The layout's `ram_1000_3dpotter`: the clay extruder as toolhead.
    clay = Flag(True)

    sidelength = beam_length + Length(2 * Cc_plastic_length)

    x = Driver(default=0.0, unit='mm', range=(-REACH, REACH))
    y = Driver(default=0.0, unit='mm', range=(-REACH, REACH))
    z = Driver(default=0.0, unit='mm', range=(0.0, Z_MAX))

    instructions = {
        'Home': Instruction({'x': 0.0, 'y': 0.0, 'z': 0.0}, duration=4.0),
        'HomeX': Instruction({'x': 0.0}, duration=2.0),
        'HomeY': Instruction({'y': 0.0}, duration=2.0),
        'HomeZ': Instruction({'z': 0.0}, duration=3.0),
        'Center': Instruction({'x': 0.0, 'y': 0.0, 'z': 400.0}, duration=3.0),
        'Lift': Instruction({'z': 900.0}, duration=4.0),
        'AnchorA': Instruction(_toward(A), duration=3.0),
        'AnchorB': Instruction(_toward(B), duration=3.0),
        'AnchorC': Instruction(_toward(C), duration=3.0),
    }

    ceiling = Ceiling(beam_length=beam_length)
    mover = Mover(beam_length=beam_length, clay=clay)
    anchors = Anchor().repeat(3)
    bed = Bed(x=BED_SIZE[0], y=BED_SIZE[1], z=BED_SIZE[2])

    #: The ceiling's internal lines, the runs down to the anchors, the
    #: three D lines and the twelve anchor segments.
    internal = Strand().repeat(19)
    runs = Strand().repeat(6)
    d_lines = MoverStrand().repeat(3)
    anchor_lines = MoverStrand().repeat(12)

    # -- where the lines run --------------------------------------------------

    def internal_segments(self):
        """The ceiling's internal segments, in the machine frame, in
        the layout's order."""
        segments = []
        for winch in (C, B, D, A):
            for start, end in layout.internal_lines(self.sidelength)[winch]:
                segments.append((apply(CEILING_LINES, start), apply(CEILING_LINES, end)))
        return segments

    def run_segments(self):
        """From each ceiling stub's far end to the nearer of its anchor's
        two low action points."""
        segments = []
        for winch in (A, B, C):
            lows = [end for end, _ in layout.anchor_segments(winch, self.sidelength)][1::2]
            for far_end, _ in layout.stubs(self.sidelength)[winch]:
                nearest = min(lows, key=lambda p: numpy.linalg.norm(p - far_end))
                segments.append((far_end, nearest))
        return segments

    def d_segments(self):
        return layout.d_segments(self.sidelength)

    def anchor_segments(self):
        return [segment for i in (A, B, C)
                for segment in layout.anchor_segments(i, self.sidelength)]

    def line_length(self, anchor):
        """The symbolic anchor distance at the drivers' pose."""
        ax, ay, az = anchors[anchor]
        lift = MOVER_LIFT[2] if anchor == D else 0.0
        return sqrt((ax - self.x) ** 2 + (ay - self.y) ** 2 + (az - self.z - lift) ** 2)

    # -- the machine -------------------------------------------------------------

    def render(self):
        place(self.ceiling, CEILING)
        for i, anchor in zip((A, B, C), self.anchors):
            place(anchor, layout.anchor_frame(i, self.sidelength))
        place(self.bed, T([BED_CENTRE[axis] - BED_SIZE[axis] / 2 for axis in range(3)]))

        for strand, (start, _) in zip(self.internal, self.internal_segments()):
            strand.translate(start.tolist())
        for strand, (start, _) in zip(self.runs, self.run_segments()):
            strand.translate(start.tolist())
        for strand, (start, _) in zip(self.d_lines, self.d_segments()):
            strand.translate(start.tolist())
        for strand, (start, _) in zip(self.anchor_lines, self.anchor_segments()):
            strand.translate(start.tolist())

    def _bind(self, strand, vector):
        """Bind a strand's far end; a plain number stays a number."""
        for value, port in zip(vector, (strand.x, strand.y, strand.z)):
            self.connect(float(value) if isinstance(value, numpy.floating) else value, port)

    def _to_mover(self, start, offset):
        """The vector from a strand's fixed end to its point on the mover."""
        shift = [float(offset[axis] - start[axis]) for axis in range(3)]
        return [self.x + shift[0], self.y + shift[1], self.z + shift[2]]

    def simulate(self):
        """Put the mover where the drivers say, redraw every line to it,
        and tell the ceiling how much line each winch has paid out."""
        self.mover.translate([self.x, self.y, self.z])

        for strand, (start, end) in zip(self.internal, self.internal_segments()):
            self._bind(strand, end - start)
        for strand, (start, end) in zip(self.runs, self.run_segments()):
            self._bind(strand, end - start)
        for strand, (start, offset) in zip(self.d_lines, self.d_segments()):
            self._bind(strand, self._to_mover(start, offset))
        for strand, (start, offset) in zip(self.anchor_lines, self.anchor_segments()):
            self._bind(strand, self._to_mover(start, offset))

        for anchor, port in zip((A, B, C, D), (self.ceiling.line_a, self.ceiling.line_b,
                                               self.ceiling.line_c, self.ceiling.line_d)):
            rest = layout.line_length(anchor, (0.0, 0.0, 0.0))
            self.connect(ADVANTAGE[anchor] * (self.line_length(anchor) - rest), port)
