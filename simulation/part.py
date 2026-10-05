"""The bases every leaf drawn from the design shares, and `place()`.

`DesignStl` is a part the layout imports as an STL; `ScadPart` is one it
calls as a module; `Strand` is a line.  `place()` puts any node where a
composed OpenSCAD transform says, as one rotation and one translation.
"""

import math

import numpy
from molejo import Circle, Line, P, Shape
from scipy.spatial.transform import Rotation
from solid2 import cube, cylinder
from machinome.motion.ports import TranslationalPort
from machinome.node.molejo import MolejoNode
from machinome.node.solid2 import Solid2Node
from machinome.node.stl import StlNode
from machinome.parameters import Flag, Length

from simulation import materials
from simulation.scad import scad_sources

#: The mirror planes a mirrored leaf may be drawn on.
MIRROR_X, MIRROR_Y = 0, 1


def place(node, matrix, mirror_axis=None):
    """Put `node` where `matrix` says, as rotate then translate.

    A matrix of negative determinant is a mirrored placement; the leaf
    must then be drawn mirrored across `mirror_axis` (its `mirrored`
    flag), and what is placed is the proper part of the transform.
    """
    rotation = numpy.array(matrix[:3, :3], dtype=float)
    if numpy.linalg.det(rotation) < 0:
        if mirror_axis is None or not getattr(node, 'mirrored', False):
            raise ValueError(f'{node.name}: a mirrored placement needs a mirrored leaf')
        flip = numpy.identity(3)
        flip[mirror_axis, mirror_axis] = -1.0
        rotation = rotation @ flip
    vector = Rotation.from_matrix(rotation).as_rotvec()
    angle = numpy.linalg.norm(vector)
    if angle > 1e-12:
        node.rotate(math.degrees(angle), (vector / angle).tolist())
    node.translate(matrix[:3, 3].tolist())
    return node


class DesignStl(StlNode):
    """A part the layout imports from `stl/`.

    `mirrored` draws the file reflected across `MIRROR_AXIS`, for the
    parts the layout places under `mirror()`.  The framework tracks the
    file and this module; the rest of the design is added so an edit to
    the sources that exported the file rebuilds it too.
    """

    color = materials.PRINTED
    MIRROR_AXIS = MIRROR_X
    mirrored = Flag(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = self.files | scad_sources()

    def adjust(self, mesh):
        if self.mirrored:
            mesh = mesh.copy()
            vertices = mesh.vertices.copy()
            vertices[:, self.MIRROR_AXIS] *= -1.0
            mesh.vertices = vertices
            mesh.invert()
        return mesh


class ScadPart(Solid2Node):
    """A part whose geometry is one of the design's own modules."""

    color = materials.PRINTED

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = self.files | scad_sources()


class Box(Solid2Node):
    """A `cube([x, y, z])`, corner at the origin, as the layout draws its
    beams, plates and boards."""

    x = Length(min=0)
    y = Length(min=0)
    z = Length(min=0)

    def render(self):
        return cube([self.x, self.y, self.z])


class Bed(Box):
    """The layout's `bed()`: 800 square, 5 thick."""

    color = materials.BED


class Rod(Solid2Node):
    """A `cylinder(d, h)` along +Z from the origin."""

    diameter = Length(min=0)
    length = Length(min=0)
    fn = 48

    def render(self):
        return cylinder(d=self.diameter, h=self.length)


class Strand(MolejoNode):
    """A line: 1 mm in radius as the layout draws it, from the node's
    origin straight to the point the ports name."""

    color = materials.LINE

    x = TranslationalPort(unit='mm')
    y = TranslationalPort(unit='mm')
    z = TranslationalPort(unit='mm')

    def render(self):
        return Shape(profile=Circle(radius=1.0),
                     path=[Line(to=[P.x, P.y, P.z])],
                     path_samples=1, profile_samples=12)


class MoverStrand(Strand):
    """A line to the mover: the layout draws those pink."""

    color = materials.MOVER_LINE
