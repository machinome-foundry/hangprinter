"""A floor anchor: `ABC_anchor()`, in its own frame.  A plywood plate
with two line roller towers, the second the layout's `mirror([0, 1,
0])` of the first, each with its bullet -- the bearing holder the line
comes down onto -- drawn assembled by the design's own `bullet()`
module rather than lying beside the tower as the STL's print layout has
it.
"""

from solid2 import mirror
from solid_node.node import AssemblyNode
from solid_node.parameters import Flag

from simulation import materials
from simulation.frames import chain
from simulation.layout import ANCHOR_PLATE, ANCHOR_PLATE_SIZE, ANCHOR_TOWERS
from simulation.part import MIRROR_Y, Box, DesignStl, ScadPart, place
from simulation.scad import line_roller_anchor


class AnchorPlate(Box):
    color = materials.ANCHOR_PLATE


class LineRollerTower(DesignStl):
    """`line_roller_anchor.stl` is a print pack: the tower, its bullet
    and two slit inserts.  The tower is this part."""
    stl_source = '../stl/line_roller_anchor.stl'
    body = 2
    MIRROR_AXIS = MIRROR_Y


class Bullet(ScadPart):
    """`bullet()`: the bearing holder slid into the tower."""

    mirrored = Flag(False)

    def render(self):
        bullet = line_roller_anchor.bullet()
        return mirror([0, 1, 0])(bullet) if self.mirrored else bullet


class Anchor(AssemblyNode):

    plate = AnchorPlate(x=ANCHOR_PLATE_SIZE[0], y=ANCHOR_PLATE_SIZE[1], z=ANCHOR_PLATE_SIZE[2])
    towers = [LineRollerTower(), LineRollerTower(mirrored=True)]
    bullets = [Bullet(), Bullet(mirrored=True)]

    def render(self):
        place(self.plate, ANCHOR_PLATE)
        for tower, bullet, matrix in zip(self.towers, self.bullets, ANCHOR_TOWERS):
            place(tower, matrix, MIRROR_Y)
            place(bullet, matrix, MIRROR_Y)
