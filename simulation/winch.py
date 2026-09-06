"""One winch of the ceiling unit: the spool stack that turns, the covers
that do not, the smooth rod, the motor with its encoder and gear, the two
belt roller bearings, and the belt between them, in the frame
`sandwich_and_motor_ABC()` draws them in -- the sandwich's base on the
origin, the spool axis along Y at `bearing_z`, the motor out along +X.

The winch reads one port, `line`: millimetres of line paid out since
the origin pose, signed so that a positive value turns the stack about
its own +Z.  The ceiling, which knows which way each winch's line leaves
its spool, supplies the sign; the winch converts millimetres to degrees
at `Spool_r`, turns the motor gear `Spool_teeth / Motor_teeth` as far the
same way, advances the belt by the spool gear's pitch-line travel and
spins the rollers under its back.

The motor bracket is a ceiling part: the four brackets are four files,
and the winches are otherwise two kinds, ABC and D.
"""

import math

import numpy
from molejo import P, Shape, Wrap
from solid_node.node import AssemblyNode, TranslationalPort
from solid_node.parameters import Flag, Length

from simulation import gt2, layout, materials
from simulation.frames import R, T, chain, direction
from simulation.layout import (
    BELT_ROLLERS,
    GT2_belt_width,
    GT2_motor_gear_teeth,
    GT2_spool_gear_teeth,
    MOTOR,
    MOTOR_GEAR,
    MOTOR_GEAR_MIRRORED,
    MOTOR_MIRRORED,
    ROTOR_ABC,
    ROTOR_D,
    SANDWICH_ABC,
    SANDWICH_ABC_PARTS,
    SANDWICH_D,
    SANDWICH_D_PARTS,
    SMOOTH_ROD_ABC,
    SMOOTH_ROD_D,
    SMOOTH_ROD_DIAMETER,
    Smooth_rod_length_ABC,
    Smooth_rod_length_D,
    Spool_r,
    b623_outer_dia,
)
from simulation.part import MIRROR_X, DesignStl, Rod, ScadPart, place
from simulation.scad import util


# --- the parts ------------------------------------------------------------------

class SpoolGear(DesignStl):
    stl_source = '../stl/GT2_spool_gear.stl'
    color = materials.SPOOL_GEAR


class Spool(DesignStl):
    stl_source = '../stl/spool.stl'


class SpoolMirrored(DesignStl):
    stl_source = '../stl/spool_mirrored.stl'


class SpoolCover(DesignStl):
    """The cover's export carries 30 loose 2 mm³ shells at its rim, its
    snap ridges exported off the wall; the wall is the part."""
    stl_source = '../stl/spool_cover.stl'
    body = 0


class SpoolCoverMirrored(DesignStl):
    stl_source = '../stl/spool_cover_mirrored.stl'
    body = 30


class DleftSpool(DesignStl):
    stl_source = '../stl/dleft_spool.stl'


class SepDisc(DesignStl):
    stl_source = '../stl/sep_disc.stl'


class DleftSpoolCover(DesignStl):
    stl_source = '../stl/dleft_spool_cover.stl'
    body = 82


class DrightSpoolTop(DesignStl):
    stl_source = '../stl/dright_spool_top.stl'


class DrightSpoolBottom(DesignStl):
    stl_source = '../stl/dright_spool_bottom.stl'


class DrightSpoolCover(DesignStl):
    stl_source = '../stl/dright_spool_cover.stl'
    body = 0


class Motor(DesignStl):
    """The whitelabel motor's body; the file's other body is the encoder."""
    stl_source = '../stl/for_render/whitelabel_motor.stl'
    body = 1
    color = materials.MOTOR


class Encoder(DesignStl):
    stl_source = '../stl/for_render/whitelabel_motor.stl'
    body = 0
    color = materials.ENCODER


class MotorGear(DesignStl):
    stl_source = '../stl/for_render/GT2_motor_gear.stl'
    color = materials.MOTOR_GEAR


class RollerBearing(ScadPart):
    """A flanged 623, as `util.scad` draws it: 10 mm across, 4 wide,
    with its 11 mm flange at the base."""
    color = materials.BEARING

    def render(self):
        return util.b623_flanged()


class SmoothRod(Rod):
    color = materials.SMOOTH_ROD


# --- the belt --------------------------------------------------------------------

#: Rings molejo spends on each of the loop's six elements.  The spool
#: gear's arc is the longest, 400 mm and 200 teeth, so this is five
#: rings a tooth there and generous everywhere else.
PATH_SAMPLES = 1024

#: The belt lies in the winch's XZ plane.  molejo draws a wrap in XY,
#: width along +Z, so the plane is turned up and the width, which then
#: runs along -Y, is centred on the spool gear.
BELT = chain(T([0, GT2_belt_width / 2, 0]), R([90, 0, 0]))


def belt_circles():
    """The three circles the loop runs on, in the wrap's plane (X the
    winch's X, Y the winch's Z): the spool gear's pitch circle, the belt
    roller with the belt's back on it, bent backwards, and the motor
    gear's pitch circle.

    The bracket puts the roller's rim exactly one belt thickness off the
    spool gear's rim (`Belt_roller_bearing_xpos`), level with the top of
    the motor gear (`Belt_roller_h`): the belt leaves the spool gear
    straight down, turns on the roller, runs level onto the motor gear,
    wraps it, and returns along the long lower span.
    """
    spool = gt2.on_pulley((0.0, layout.bearing_z), gt2.pulley_radius(GT2_spool_gear_teeth))
    roller = {'center': list(layout.BELT_ROLLER_CENTRE),
              'radius': b623_outer_dia / 2 + gt2.BACK,
              'turn': 'counterclockwise'}
    motor = gt2.on_pulley((layout.MOTOR_SHAFT[0], layout.MOTOR_SHAFT[2]),
                          gt2.pulley_radius(GT2_motor_gear_teeth))
    return [spool, roller, motor]


#: The spool gear's pitch radius: what a degree of spool turn is worth in belt.
SPOOL_PITCH_RADIUS = belt_circles()[0]['radius']
ROLLER_RADIUS = b623_outer_dia / 2
GEAR_RATIO = GT2_spool_gear_teeth / GT2_motor_gear_teeth


class Belt(gt2.Belt):
    """The winch's GT2 loop, 6.5 mm wide, teeth inward, 303 of them."""

    travel = TranslationalPort(unit='mm')

    def render(self):
        circles = belt_circles()
        return Shape(
            profile=gt2.section(GT2_belt_width),
            path=[Wrap(around=circles, teeth=gt2.teeth(circles), phase=P.travel)],
            path_samples=PATH_SAMPLES,
            profile_samples=4,
            loop=True,
        )


# --- the stacks that turn ----------------------------------------------------------

class RotorABC(AssemblyNode):
    """`sandwich_ABC()` less its covers: gear and two spools, on the
    sandwich's own axis."""

    spool_gear = SpoolGear()
    spool_mirrored = SpoolMirrored()
    spool = Spool()

    def render(self):
        for name in ROTOR_ABC:
            place(getattr(self, name), SANDWICH_ABC_PARTS[name])


class RotorD(AssemblyNode):
    """`sandwich_D()` less its covers: gear, the left spool with its
    separator disc, the right spool's two halves."""

    spool_gear = SpoolGear()
    dleft_spool = DleftSpool()
    sep_disc = SepDisc()
    dright_spool_top = DrightSpoolTop()
    dright_spool_bottom = DrightSpoolBottom()

    def render(self):
        for name in ROTOR_D:
            place(getattr(self, name), SANDWICH_D_PARTS[name])


# --- the senses, from the placements ------------------------------------------------

def _axis(matrix):
    return direction(matrix, (0, 0, 1))


def _sign(a, b):
    return 1.0 if float(numpy.dot(a, b)) > 0 else -1.0


WRAP_NORMAL = _axis(BELT)
GEAR_AXIS = _axis(MOTOR_GEAR)
ROLLER_AXES = [_axis(matrix) for matrix in BELT_ROLLERS]


def _turn(winch, rotor_axis):
    """Turn everything by the line the port says was paid out."""
    paid = winch.line.value
    if paid is None:
        paid = 0.0
    radians = paid / Spool_r
    degrees = radians * 180.0 / math.pi
    winch.rotor.rotate(degrees, [0, 0, 1])
    # a leaf drawn mirrored turns the other way about its own axis for the
    # same turn in the world: its frame is a reflection of the design's
    handed = -1.0 if winch.motor_gear.mirrored else 1.0
    winch.motor_gear.rotate(handed * _sign(GEAR_AXIS, rotor_axis) * GEAR_RATIO * degrees,
                            [0, 0, 1])
    winch.connect(_sign(rotor_axis, WRAP_NORMAL) * radians * SPOOL_PITCH_RADIUS,
                  winch.belt.travel)
    for roller, axis in zip(winch.rollers, ROLLER_AXES):
        roller.rotate(-_sign(axis, rotor_axis) * degrees * SPOOL_PITCH_RADIUS / ROLLER_RADIUS,
                      [0, 0, 1])


class WinchABC(AssemblyNode):
    """`sandwich_and_motor_ABC()`, less the bracket and the deflector.

    `left_handed` is the layout's `mirror([1, 0, 0])` on the motor and
    its gear, for winches A and B.
    """

    left_handed = Flag(False)

    rotor = RotorABC()
    spool_cover = SpoolCover()
    spool_cover_mirrored = SpoolCoverMirrored()
    rod = SmoothRod(diameter=SMOOTH_ROD_DIAMETER, length=Smooth_rod_length_ABC)
    motor = Motor(mirrored=left_handed)
    encoder = Encoder(mirrored=left_handed)
    motor_gear = MotorGear(mirrored=left_handed)
    rollers = RollerBearing().repeat(2)
    belt = Belt()

    line = TranslationalPort(unit='mm')

    #: The stack's axis in the winch frame.
    AXIS = _axis(SANDWICH_ABC)

    def render(self):
        place(self.rotor, SANDWICH_ABC)
        for name in ('spool_cover', 'spool_cover_mirrored'):
            place(getattr(self, name), chain(SANDWICH_ABC, SANDWICH_ABC_PARTS[name]))
        place(self.rod, chain(SMOOTH_ROD_ABC, T([0, 0, -Smooth_rod_length_ABC / 2])))
        motor, gear = (MOTOR_MIRRORED, MOTOR_GEAR_MIRRORED) if self.left_handed else (MOTOR, MOTOR_GEAR)
        place(self.motor, motor, MIRROR_X)
        place(self.encoder, motor, MIRROR_X)
        place(self.motor_gear, gear, MIRROR_X)
        for roller, matrix in zip(self.rollers, BELT_ROLLERS):
            place(roller, matrix)
        place(self.belt, BELT)

    def simulate(self):
        _turn(self, self.AXIS)


class WinchD(AssemblyNode):
    """`sandwich_and_motor_D()`, less the bracket: the three-line spool."""

    rotor = RotorD()
    dleft_spool_cover = DleftSpoolCover()
    dright_spool_cover = DrightSpoolCover()
    rod = SmoothRod(diameter=SMOOTH_ROD_DIAMETER, length=Smooth_rod_length_D)
    motor = Motor()
    encoder = Encoder()
    motor_gear = MotorGear()
    rollers = RollerBearing().repeat(2)
    belt = Belt()

    line = TranslationalPort(unit='mm')

    AXIS = _axis(SANDWICH_D)

    def render(self):
        place(self.rotor, SANDWICH_D)
        for name in ('dleft_spool_cover', 'dright_spool_cover'):
            place(getattr(self, name), chain(SANDWICH_D, SANDWICH_D_PARTS[name]))
        place(self.rod, chain(SMOOTH_ROD_D, T([0, 0, -Smooth_rod_length_D / 2])))
        place(self.motor, MOTOR)
        place(self.encoder, MOTOR)
        place(self.motor_gear, MOTOR_GEAR)
        for roller, matrix in zip(self.rollers, BELT_ROLLERS):
            place(roller, matrix)
        place(self.belt, BELT)

    def simulate(self):
        _turn(self, self.AXIS)
