"""Measurements the contracts share: what turned, by how much, about
which axis; where a strand's ends are; how the design's CSG leaves
match the model's nodes.

This module defines no node and is imported only by tests.
"""

import math

import numpy
import trimesh


def turned(node, before, axis_point, axis_direction):
    """Degrees `node` has turned about the axis through `axis_point`
    along `axis_direction` since its world vertices were `before`,
    signed by the right hand about the direction, read vertex by vertex
    (a moved mesh keeps its vertex order) and taken as the median of
    the vertices that stand off the axis."""
    axis = numpy.asarray(axis_direction, dtype=float)
    axis = axis / numpy.linalg.norm(axis)
    after = node.mesh.vertices
    u = _perpendicular(axis)
    v = numpy.cross(axis, u)
    r0 = numpy.asarray(before) - axis_point
    r1 = after - axis_point
    a0 = numpy.arctan2(r0 @ v, r0 @ u)
    a1 = numpy.arctan2(r1 @ v, r1 @ u)
    far = numpy.hypot(r0 @ u, r0 @ v) > 2.0
    delta = numpy.degrees(numpy.angle(numpy.exp(1j * (a1 - a0))))
    return float(numpy.median(delta[far]))


def moved(node, before):
    """How far `node`'s vertices moved since `before`, as the common
    displacement, and the largest departure from it."""
    shift = node.mesh.vertices - numpy.asarray(before)
    common = shift.mean(axis=0)
    return common, float(numpy.abs(shift - common).max())


def _perpendicular(axis):
    other = numpy.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else numpy.array([0.0, 1.0, 0.0])
    u = numpy.cross(axis, other)
    return u / numpy.linalg.norm(u)


def strand_ends(node):
    """The centres of a strand's two end rings, in world coordinates."""
    vertices = node.mesh.vertices
    axis = vertices.mean(axis=0)
    direction = numpy.linalg.svd(vertices - axis)[2][0]
    along = (vertices - axis) @ direction
    near = vertices[along < along.min() + 0.01].mean(axis=0)
    far = vertices[along > along.max() - 0.01].mean(axis=0)
    return near, far


def strand_length(node):
    near, far = strand_ends(node)
    return float(numpy.linalg.norm(far - near))


def same_segment(ends, start, end, tolerance):
    """Whether a strand's ends are `start` and `end`, either way round."""
    a, b = ends
    return ((numpy.linalg.norm(a - start) < tolerance and numpy.linalg.norm(b - end) < tolerance)
            or (numpy.linalg.norm(a - end) < tolerance and numpy.linalg.norm(b - start) < tolerance))


def local_vertices(node):
    """A rigid node's artifact vertices in its own frame."""
    return numpy.asarray(trimesh.load(node.stl_file, force='mesh').vertices)


def placement_error(node, matrix, mirror_axis=None):
    """The largest distance between `node`'s world vertices and its
    local vertices carried by `matrix`; for a node drawn mirrored, the
    matrix is the design's (mirror included) and the local vertices are
    unmirrored first."""
    local = local_vertices(node)
    if mirror_axis is not None:
        local = local.copy()
        local[:, mirror_axis] *= -1.0
    expected = (matrix[:3, :3] @ local.T).T + matrix[:3, 3]
    return float(numpy.abs(node.mesh.vertices - expected).max())


def stl_nodes(node):
    """Every node below `node` drawn from a design STL, with the file it
    is drawn from relative to the design's `src/`."""
    found = []
    if getattr(node, 'stl_source', None):
        found.append(node)
    for child in getattr(node, 'children', None) or []:
        found.extend(stl_nodes(child))
    return found


def design_file(node):
    """`../stl/...` as the layout writes it."""
    source = node.stl_source
    return '../stl/' + source.split('/stl/', 1)[1]


def radial_distances(vertices, axis_point, axis_direction):
    axis = numpy.asarray(axis_direction, dtype=float)
    axis = axis / numpy.linalg.norm(axis)
    r = numpy.asarray(vertices) - axis_point
    along = r @ axis
    return numpy.linalg.norm(r - numpy.outer(along, axis), axis=1), along


def profile_shift(angles0, radii0, angles1, radii1, step, window):
    """How far, in degrees, the radius-against-angle pattern moved from
    (`angles0`, `radii0`) to (`angles1`, `radii1`): the shift `s` for
    which `radii1(a + s) == radii0(a)`, a feature at `a` now at `a + s`,
    searched over ±`window` degrees in `step` degrees."""
    lo = max(angles0.min(), angles1.min()) + window
    hi = min(angles0.max(), angles1.max()) - window
    grid = numpy.arange(lo, hi, step)
    base = numpy.interp(grid, *_sorted(angles0, radii0))
    best, best_score = 0.0, -numpy.inf
    for shift in numpy.arange(-window, window + step / 2, step):
        moved_profile = numpy.interp(grid + shift, *_sorted(angles1, radii1))
        score = -float(numpy.abs(moved_profile - base).mean())
        if score > best_score:
            best, best_score = float(shift), score
    return best


def _sorted(angles, radii):
    order = numpy.argsort(angles)
    return angles[order], radii[order]


# --- interference, decided on the engine -----------------------------------------

#: Below this the engine's intersection volume is float noise from
#: coincident faces, which the design has wherever two parts of a stack
#: meet face to face.  The framework's own verdict reads any nonzero
#: number, even a negative one, as interference (see the design record);
#: this sweep reads contact as contact.
NOISE = 1e-6


def printed_solids(node):
    """The topmost rigid nodes below `node`: the printed solids."""
    if getattr(node, 'rigid', False):
        return [node]
    found = []
    for child in getattr(node, 'children', None) or []:
        found.extend(printed_solids(child))
    return found


def _solid(mesh):
    from manifold3d import Manifold, Mesh
    return Manifold(mesh=Mesh(
        vert_properties=numpy.asarray(mesh.vertices, numpy.float64),
        tri_verts=numpy.asarray(mesh.faces, numpy.uint32)))


def shared_volume(node1, node2):
    """The volume two rigid nodes share at the current instant, in mm³."""
    result = _solid(node1.mesh) ^ _solid(node2.mesh)
    return 0.0 if result.is_empty() else float(result.volume())


def interferences(node, among=None, against=None):
    """Every pair of printed solids below `node` sharing more than
    `NOISE` mm³, as (a, b, volume).  `among` restricts the first side
    and `against` the second; both default to every solid."""
    solids = printed_solids(node)
    first = among if among is not None else solids
    second = against if against is not None else solids
    meshes = {id(s): s.mesh for s in set(first) | set(second)}
    bounds = {key: mesh.bounds for key, mesh in meshes.items()}
    found = []
    seen = set()
    for a in first:
        for b in second:
            if a is b or (id(b), id(a)) in seen or (id(a), id(b)) in seen:
                continue
            seen.add((id(a), id(b)))
            lo = numpy.maximum(bounds[id(a)][0], bounds[id(b)][0])
            hi = numpy.minimum(bounds[id(a)][1], bounds[id(b)][1])
            if (hi < lo).any():
                continue
            result = _solid(meshes[id(a)]) ^ _solid(meshes[id(b)])
            volume = 0.0 if result.is_empty() else float(result.volume())
            if volume > NOISE:
                found.append((a, b, volume))
    return found
