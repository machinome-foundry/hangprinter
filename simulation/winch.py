"""One winch of the ceiling unit: the spool stack that turns, the covers
that do not, the smooth rod, the motor with its encoder and gear, the two
belt roller bearings, and the belt between them, in the frame
`sandwich_and_motor_ABC()` draws them in -- the sandwich's base on the
origin, the spool axis along Y at `bearing_z`, the motor out along +X.

The stack is one revolute joint (`RotorABC.turn` / `RotorD.turn`); the
root binds it to the line the winch pays out.  Everything below the
stack is a transmission stated as a relation, by ratio: the motor gear
turns `Spool_teeth / Motor_teeth` as far the same way, the belt advances
by the spool gear's pitch-line travel, and the two roller bearings spin
under its back.

The motor bracket is a ceiling part: the four brackets are four files,
and the winches are otherwise two kinds, ABC and D.
"""

import math

import numpy
from molejo import P, Shape, Wrap
from machinome.motion.joints import Revolute
from machinome.motion.ports import TranslationalPort
from machinome.node.assembly import AssemblyNode
from machinome.parameters import Flag, Length
from machinome.mechanics import rolling_travel

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
    b623_outer_dia,
)
from simulation.part import MIRROR_X, DesignStl, Rod, ScadPart, place
from simulation.scad import util


# --- the shared shaft axis --------------------------------------------------------

#: The direction every motor gear and both belt roller bearings turn
#: about, in every winch: the motor shaft's own axis, the winch frame's
#: Y.  Declaring a leaf's joint about this shared axis, rather than
#: about the leaf's own placed +Z, is what lets one declaration serve
#: both the unmirrored and the mirrored leaf: the framework carries this
#: direction into each body's own frame and finds the local axis
#: mirrored gears turn about there too.
SHAFT_AXIS = (0.0, 1.0, 0.0)

#: `BELT_ROLLER_CENTRE` read back into three dimensions: the point both
#: roller bearings share on the shaft axis -- `belt_roller_bearings()`
#: offsets them from it along Y, in opposite directions, so one anchor
#: serves both copies.
BELT_ROLLER_AXIS = (layout.BELT_ROLLER_CENTRE[0], 0.0, layout.BELT_ROLLER_CENTRE[1])

#: `layout.MOTOR_SHAFT` read back as plain floats: the point every motor
#: gear's own axis passes through, in the winch frame -- the mirrored
#: placement differs from the unmirrored one only by a mirror whose
#: displacement is along this same shaft, so one anchor, stated at each
#: site, serves the mirrored and unmirrored leaf alike.
MOTOR_SHAFT = tuple(float(v) for v in layout.MOTOR_SHAFT)


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
    """The mirrored placement (`MOTOR_GEAR_MIRRORED`) differs from the
    unmirrored one only by a mirror in the bracket frame whose
    displacement is along the shaft, so mirrored and unmirrored gears
    sit on one line and one declaration, stated at each site, serves
    both -- `turn` is declared where each winch places its own
    `motor_gear`, not here."""
    stl_source = '../stl/for_render/GT2_motor_gear.stl'
    color = materials.MOTOR_GEAR


class RollerBearing(ScadPart):
    """A flanged 623, as `util.scad` draws it: 10 mm across, 4 wide,
    with its 11 mm flange at the base. `spin` is declared where each
    winch places its own `rollers` repeat, not here: the shaft axis and
    the belt roller axis are the winch's own frame's, and one site
    declaration on the repeat carries both copies through their own
    rest placement."""
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
#: The roller's turn for the spool's: the belt's back drives it at the
#: spool gear's pitch radius over the roller's own.
ROLLER_RATIO = SPOOL_PITCH_RADIUS / ROLLER_RADIUS
#: A degree of spool turn, in millimetres of belt (the spool gear's
#: pitch-line travel).
BELT_MM_PER_DEGREE = rolling_travel(1.0, SPOOL_PITCH_RADIUS)


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


# --- the axis and sign helpers ------------------------------------------------------

def _axis(matrix):
    return direction(matrix, (0, 0, 1))


def _sign(a, b):
    return 1.0 if float(numpy.dot(a, b)) > 0 else -1.0


WRAP_NORMAL = _axis(BELT)


# --- the stacks that turn ----------------------------------------------------------

class RotorABC(AssemblyNode):
    """`sandwich_ABC()` less its covers: gear and two spools, on the
    sandwich's own axis."""

    turn = Revolute(axis=(0.0, 0.0, 1.0), unit='deg')

    spool_gear = SpoolGear()
    spool_mirrored = SpoolMirrored()
    spool = Spool()

    def render(self):
        for name in ROTOR_ABC:
            place(getattr(self, name), SANDWICH_ABC_PARTS[name])


class RotorD(AssemblyNode):
    """`sandwich_D()` less its covers: gear, the left spool with its
    separator disc, the right spool's two halves."""

    turn = Revolute(axis=(0.0, 0.0, 1.0), unit='deg')

    spool_gear = SpoolGear()
    dleft_spool = DleftSpool()
    sep_disc = SepDisc()
    dright_spool_top = DrightSpoolTop()
    dright_spool_bottom = DrightSpoolBottom()

    def render(self):
        for name in ROTOR_D:
            place(getattr(self, name), SANDWICH_D_PARTS[name])


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
    motor_gear = MotorGear(mirrored=left_handed,
                            turn=Revolute(axis=SHAFT_AXIS, at=MOTOR_SHAFT, unit='deg'))
    rollers = RollerBearing(spin=Revolute(axis=SHAFT_AXIS, at=BELT_ROLLER_AXIS,
                                          unit='deg')).repeat(2)
    belt = Belt()

    #: The stack's axis in the winch frame.
    AXIS = _axis(SANDWICH_ABC)

    #: Which way the stack's own axis points against the shared shaft
    #: axis: both pulleys are inside the toothed loop, so the motor gear
    #: turns the stack's way at the tooth ratio, and the framework finds
    #: this same sign on the gear's own mirrored or unmirrored placement.
    SENSE = _sign(SHAFT_AXIS, AXIS)          # -1
    #: molejo circulates the tooth pattern against the loop's clockwise
    #: run for a positive phase, so the belt travels with the gear when
    #: its phase is the pitch-line travel taken the other way round the
    #: wrap normal.
    BELT_SENSE = -_sign(AXIS, WRAP_NORMAL)   # -1

    rotor.drives(motor_gear.turn, ratio=SENSE * GEAR_RATIO)
    rotor.drives(belt.travel, ratio=BELT_SENSE * BELT_MM_PER_DEGREE)
    rotor.drives(rollers.spin, ratio=-SENSE * ROLLER_RATIO)

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
        if self.rotor.turn.value is None:    # a winch built on its own stands still
            self.rotor.turn = 0.0


class WinchD(AssemblyNode):
    """`sandwich_and_motor_D()`, less the bracket: the three-line spool."""

    rotor = RotorD()
    dleft_spool_cover = DleftSpoolCover()
    dright_spool_cover = DrightSpoolCover()
    rod = SmoothRod(diameter=SMOOTH_ROD_DIAMETER, length=Smooth_rod_length_D)
    motor = Motor()
    encoder = Encoder()
    motor_gear = MotorGear(turn=Revolute(axis=SHAFT_AXIS, at=MOTOR_SHAFT, unit='deg'))
    rollers = RollerBearing(spin=Revolute(axis=SHAFT_AXIS, at=BELT_ROLLER_AXIS,
                                          unit='deg')).repeat(2)
    belt = Belt()

    AXIS = _axis(SANDWICH_D)

    SENSE = _sign(SHAFT_AXIS, AXIS)          # +1
    BELT_SENSE = -_sign(AXIS, WRAP_NORMAL)   # +1

    rotor.drives(motor_gear.turn, ratio=SENSE * GEAR_RATIO)
    rotor.drives(belt.travel, ratio=BELT_SENSE * BELT_MM_PER_DEGREE)
    rotor.drives(rollers.spin, ratio=-SENSE * ROLLER_RATIO)

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
        if self.rotor.turn.value is None:    # a winch built on its own stands still
            self.rotor.turn = 0.0
