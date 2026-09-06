"""OpenSCAD's transforms as matrices, so a placement can be written in
the layout's own reading order and checked against the layout's own
CSG export.

`chain(T([...]), R([...]), Rz(-90))` is `translate([...]) rotate([...])
rotate([0, 0, -90]) child` -- outermost first, as the .scad reads.
`place()` in `part.py` turns such a matrix into a node's rotate and
translate operations.  This module defines no node.
"""

import math

import numpy


def T(vector):
    matrix = numpy.identity(4)
    matrix[:3, 3] = vector
    return matrix


def Rx(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return numpy.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], dtype=float)


def Ry(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return numpy.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], dtype=float)


def Rz(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return numpy.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)


def R(angles):
    """OpenSCAD's `rotate([a, b, c])`: about X by a, then Y by b, then Z by c."""
    a, b, c = angles
    return Rz(c) @ Ry(b) @ Rx(a)


def M(normal):
    """OpenSCAD's `mirror([x, y, z])`."""
    n = numpy.array(normal, dtype=float)
    n /= numpy.linalg.norm(n)
    matrix = numpy.identity(4)
    matrix[:3, :3] -= 2.0 * numpy.outer(n, n)
    return matrix


def chain(*matrices):
    """The composed transform of nested OpenSCAD operations, outermost first."""
    result = numpy.identity(4)
    for matrix in matrices:
        result = result @ matrix
    return result


def apply(matrix, point):
    """A point carried by `matrix`."""
    return (matrix @ numpy.array([*point, 1.0]))[:3]


def direction(matrix, vector):
    """A direction carried by `matrix` (no translation)."""
    return matrix[:3, :3] @ numpy.array(vector, dtype=float)


def rotation2(point, degrees):
    """The layout's `rotation(v, ang)`: about Z, in the XY plane."""
    return apply(Rz(degrees), point)
