"""The design's numbers and the layout's placements, restated.

Everything here is read off `src/lib/parameters.scad` and
`src/layout.scad` and kept under the design's own names, in the
layout's own nesting order, so a reader can hold the two side by side.
`test_layout.py` asks OpenSCAD for the same expressions and compares.

Two frames matter.  The **machine** frame is the layout's: the
calibrated nozzle origin on the bed, Z up, the `anchors` table in it.
The **ceiling** frame is the one `full_winch()` is drawn in -- Z up off
the plate -- and the layout hangs it under anchor D upside down through
`CEILING`; it draws the ceiling's internal lines through `CEILING_LINES`,
ten millimetres higher and without anchor D's X offset (a design quirk,
kept).  Every function taking `sidelength` takes the machine's, since
the beam length is a knob.

This module defines no node.
"""

import math

import numpy

from simulation.frames import M, R, Rz, T, apply, chain, rotation2

# --- parameters.scad --------------------------------------------------------

Base_th = 2
Beam_width = 15
Wiggle = 0.25
Fat_beam_width = Beam_width + Wiggle
Beam_length = 400
Wall_th = 2.5
Nema17_cube_width = 42.43
b608_outer_dia = 22.2
b608_width = 7.05
b608_vgroove_small_r = b608_outer_dia / 2 + 0.5
Gap_between_sandwich_and_plate = 1.5 + Base_th
Cc_l1 = (Fat_beam_width + 2 * Wall_th) * 2 * math.sqrt(3)
Cc_rad_b = 4
Cc_action_point_from_mid = Cc_l1 / math.sqrt(3) - 2 * Cc_rad_b - 7
Cc_plastic_length = math.sqrt(Cc_action_point_from_mid ** 2 - (Cc_action_point_from_mid / 2) ** 2)
Move_d_bearings_inwards = -2
Spool_r = 75
Spool_height = 8
Sep_disc_radius = (161.83 + 1) / 2
b623_width = 4
b623_outer_dia = 10
b623_big_ugroove_big_r = (12 + 3) / 2
b623_big_ugroove_small_r = (10 + 3) / 2
b623_ugroove_room_to_grow_r = 1.1
Depth_of_roller_base = 18
Line_roller_ABC_winch_h = (Gap_between_sandwich_and_plate + Sep_disc_radius - Spool_r
                           + Depth_of_roller_base / 2 + b608_vgroove_small_r)
Corner_clamp_bearings_center_to_center = max(
    15, (b623_big_ugroove_big_r + b623_ugroove_room_to_grow_r) * 2 + 5)
GT2_belt_width = 6.5
GT2_gear_height = GT2_belt_width + 2
GT2_motor_gear_height = 16
GT2_motor_gear_outer_dia = 16
GT2_spool_gear_teeth = 255
GT2_motor_gear_teeth = 20
Torx_depth = GT2_gear_height / 2
Belt_roller_h = 56
Belt_thickness = 1.4
Sandwich_ABC_width = 2 * (1 + Spool_height) + GT2_gear_height
Sandwich_D_width = 4 * (1 + Spool_height) + GT2_gear_height
Spool_core_halve_width = 14.3
Spool_core_impression_in_spool_cover = 0
Spool_cover_bottom_th = 1.5
Spool_cover_shoulder = 2
Spool_cover_tot_height = Spool_cover_bottom_th + Spool_cover_shoulder + 1 + Spool_height
Smooth_rod_length_ABC = Sandwich_ABC_width + 2 * (
    Spool_core_halve_width - Spool_core_impression_in_spool_cover
    + Spool_cover_bottom_th + Spool_cover_shoulder)
Smooth_rod_length_D = Sandwich_D_width + 2 * (
    Spool_core_halve_width - Spool_core_impression_in_spool_cover
    + Spool_cover_bottom_th + Spool_cover_shoulder)
spd = Spool_height + GT2_gear_height
Belt_roller_bearing_xpos = Sep_disc_radius + b623_outer_dia / 2 + Belt_thickness
Yshift_top_plate = -297.8
Ram_1000_3dpotter_tube_inner_d = 70
Ram_1000_3dpotter_tube_outer_d = Ram_1000_3dpotter_tube_inner_d + 2 * 3.3


def sidelength(beam_length=Beam_length):
    """`Sidelength`: the distance between the mover's two action points."""
    return beam_length + 2 * Cc_plastic_length


# --- layout.scad: the machine ------------------------------------------------

A, B, C, D = 0, 1, 2, 3
X, Y, Z = 0, 1, 2
WINCH_NAMES = 'ABCD'

ram_1000_3dpotter_height_diff = 350

#: The firmware's anchor coordinates, less the clay extruder's height.
anchors = numpy.array([
    [16.83, -1584.86, -113.17 - ram_1000_3dpotter_height_diff],
    [1290.18, 1229.19, -157.45 - ram_1000_3dpotter_height_diff],
    [-1409.88, 742.61, -151.80 - ram_1000_3dpotter_height_diff],
    [21.85, -0.16, 2343.67 - ram_1000_3dpotter_height_diff],
])

length_of_toolhead = 77

#: The ceiling unit, hung under anchor D; and the frame its internal
#: lines are drawn in.
CEILING = chain(T(anchors[D] + [0, 0, 33]), R([180, 0, 0]))
CEILING_LINES = chain(T([0, 0, 43 + anchors[D][Z]]), R([180, 0, 0]))

#: The bed: 800 square, 5 thick, its top at the origin's level less 350.
BED_SIZE = (800, 800, 5)
BED_CENTRE = (-14, 91, -2.5 - ram_1000_3dpotter_height_diff)
BED_TOP = BED_CENTRE[2] + BED_SIZE[2] / 2


# --- layout.scad: the ceiling unit ------------------------------------------

dspool_y = -50 + 30
bcspool_y = -40
aspool_y = -20
aspool_lineroller_y = -110
abc_sep = 105 + 18
move_BC_deflectors = -113
extra_space_in_middle = -10

lxm1 = -abc_sep / 2 - extra_space_in_middle - spd / 2 - 1 - Spool_height
lx0 = -abc_sep / 2 - extra_space_in_middle - spd / 2
lx1 = -abc_sep / 2 - extra_space_in_middle + spd / 2
lx2 = -abc_sep / 2 - extra_space_in_middle + spd / 2 + 1 + Spool_height
lx3 = abc_sep / 2 + extra_space_in_middle - spd / 2


def ly2(sidelength):
    return sidelength / math.sqrt(12) - 50


cx = 452.17 + math.sqrt(12) * Move_d_bearings_inwards / 2
cy = 450.02 + Move_d_bearings_inwards / 2
bc_x_pos = cx / 2 - GT2_gear_height / 2 - Spool_cover_tot_height - Spool_core_halve_width - 2

#: `full_winch()`: where each winch stands in the ceiling frame.
WINCH_STATIONS = {
    A: chain(T([lx3 + spd / 2, aspool_y, 0]), Rz(-90)),
    C: chain(T([-bc_x_pos, bcspool_y, 0]), Rz(90)),
    B: chain(T([bc_x_pos, bcspool_y, 0]), Rz(90)),
    D: chain(T([-abc_sep / 2 - extra_space_in_middle, dspool_y, 0]), Rz(-90)),
}

#: The height of the spool and gear axis over the plate.
bearing_z = Sep_disc_radius + Gap_between_sandwich_and_plate

#: The line's tangent height: where the internal lines run.
hz = Gap_between_sandwich_and_plate + Sep_disc_radius - Spool_r

# `sandwich_ABC()`, in the sandwich's own frame (gear axis along Z)
SANDWICH_ABC = chain(T([0, Sandwich_ABC_width / 2, bearing_z]), R([90, 0, 0]))
SANDWICH_ABC_PARTS = {
    'spool_gear': chain(T([0, 0, 1 + Spool_height])),
    'spool_mirrored': chain(T([0, 0, 1 + Spool_height]),
                            T([0, 0, Torx_depth + 1 + Spool_height + GT2_gear_height / 2]),
                            R([0, 180, 0])),
    'spool_cover': chain(T([0, 0, 1 + Spool_height]),
                         T([0, 0, Torx_depth + 1 + Spool_height + GT2_gear_height / 2]),
                         R([0, 180, 0]),
                         T([0, 0, -Spool_cover_bottom_th - Spool_cover_shoulder]),
                         Rz(-90)),
    'spool': chain(),
    'spool_cover_mirrored': chain(T([0, 0, -Spool_cover_bottom_th - Spool_cover_shoulder]),
                                  Rz(90)),
}

# `placed_sandwich_D()` and `sandwich_D()`
SANDWICH_D = chain(T([0, -1 - Spool_height - GT2_gear_height / 2, bearing_z]),
                   R([90, 0, 180]))
_D_FLIP = chain(T([0, 0, 1 + Spool_height]),
                T([0, 0, Torx_depth + 2 * (1 + Spool_height) + GT2_gear_height / 2]),
                R([0, 180, 0]))
SANDWICH_D_PARTS = {
    'spool_gear': chain(T([0, 0, 1 + Spool_height])),
    'dleft_spool': _D_FLIP,
    'sep_disc': chain(_D_FLIP, T([0, 0, 1 + Spool_height])),
    'dleft_spool_cover': chain(_D_FLIP,
                               T([0, 0, -Spool_cover_bottom_th - Spool_cover_shoulder]),
                               Rz(90)),
    'dright_spool_top': chain(),
    'dright_spool_bottom': chain(T([0, 0, -Spool_height - 1])),
    'dright_spool_cover': chain(
        T([0, 0, -Spool_cover_bottom_th - Spool_cover_shoulder - Spool_height - 1]),
        Rz(-90)),
}

#: The stack that turns: everything in a sandwich but the covers.
ROTOR_ABC = ('spool_gear', 'spool_mirrored', 'spool')
ROTOR_D = ('spool_gear', 'dleft_spool', 'sep_disc', 'dright_spool_top', 'dright_spool_bottom')

# `render_motor_and_bracket()` under `translate([Belt_roller_bearing_xpos, 0, 0])
# rotate([0, 0, 90])`, in the winch frame.  The motor and its gear are
# mirrored in X on the left-handed winches A and B.
BRACKET = chain(T([Belt_roller_bearing_xpos, 0, 0]), Rz(90))
MOTOR = chain(BRACKET, T([-13.5, -33, 35]))
MOTOR_MIRRORED = chain(BRACKET, M([1, 0, 0]), T([-13.5, -33, 35]))
_GEAR_X = -GT2_motor_gear_height + 1.5 + (GT2_motor_gear_height - 7.4 - 1.5) / 2
MOTOR_GEAR = chain(BRACKET, T([_GEAR_X, 0, 0]), T([0, -33, 35]), R([0, 90, 0]))
MOTOR_GEAR_MIRRORED = chain(BRACKET, M([1, 0, 0]), T([_GEAR_X, 0, 0]), T([0, -33, 35]),
                            R([0, 90, 0]))

#: The motor shaft's axis in the winch frame: along Y, through this point.
MOTOR_SHAFT = apply(chain(BRACKET, T([0, -33, 35])), (0, 0, 0))

# `belt_roller_bearings()`: two flanged 623s side by side, flanges out
belt_roller_bearing_center_z = Belt_roller_h - Depth_of_roller_base / 2
BELT_ROLLERS = [
    chain(T([Belt_roller_bearing_xpos, 0, 0]), T([0, 0, belt_roller_bearing_center_z]),
          R([rot, 0, 0]), T([0, 0, -b623_width - 0.1]))
    for rot in (90, -90)
]
BELT_ROLLER_CENTRE = (Belt_roller_bearing_xpos, belt_roller_bearing_center_z)

# the smooth rods
SMOOTH_ROD_ABC = chain(T([0, 0, bearing_z]), R([90, 0, 0]))
SMOOTH_ROD_D = chain(T([0, -Smooth_rod_length_D, bearing_z]), R([90, 0, 0]),
                     T([0, 0, (Sandwich_ABC_width - Sandwich_D_width) / 2]))
SMOOTH_ROD_DIAMETER = 8

# `tilted_line_deflector_for_layout()` and where the winches put it
TILTED_DEFLECTOR = chain(T([-10, 0, 0]), Rz(-90))
DEFLECTOR_A = chain(T([move_BC_deflectors + spd / math.sqrt(3) + 1,
                       GT2_gear_height / 2 + Spool_height / 2, 0]),
                    Rz(180), TILTED_DEFLECTOR)
LINE_GUIDES_BC = chain(T([move_BC_deflectors + spd / math.sqrt(3) + 1, spd / 2, 0]),
                       Rz(180), TILTED_DEFLECTOR)
DEFLECTOR_B = chain(M([0, 1, 0]), LINE_GUIDES_BC)
DEFLECTOR_C = LINE_GUIDES_BC


def line_deflector(rot_around_center):
    """`line_deflector(rot, center=true)`."""
    return chain(Rz(rot_around_center), T([0, b623_big_ugroove_small_r - 3, 0]),
                 R([-90, 0, 0]))


def verticalizers(sidelength):
    """`placed_line_verticalizer()`: the three verticalizers."""
    angs = [180 + 30, 180, 180 - 30]
    three = [0, 120, 240]
    return [chain(Rz(-30 + three[k]),
                  T([-sidelength / math.sqrt(3) - Move_d_bearings_inwards, 0, 0]),
                  Rz(angs[k]), R([0, -90, 0]))
            for k in range(3)]


def horizontal_deflectors(sidelength):
    """`placed_line_verticalizer()`: the four horizontal deflectors."""
    y = (sidelength / math.sqrt(12) + Move_d_bearings_inwards / 2
         - b623_big_ugroove_small_r - b623_width / 2 - 1)
    return [
        chain(T([lx0 - b623_big_ugroove_small_r, y, 0]), line_deflector(-67)),
        chain(T([lx1 + b623_big_ugroove_small_r, y, 0]), line_deflector(67)),
        chain(T([lx2 + b623_big_ugroove_small_r, ly2(sidelength) - b623_big_ugroove_small_r, 0]),
              line_deflector(63)),
        chain(T([-b623_big_ugroove_small_r + b623_width / 2 + 1,
                 ly2(sidelength) - b623_big_ugroove_small_r, 0]),
              line_deflector(-90 - 90 - 90)),
    ]


WIRE_REWINDER = chain(T([lxm1, 79, 0]), Rz(90))

# `placed_landing_brackets()`
_push = 23
LANDING_BRACKETS = {
    'a': chain(T([0, 128 - b623_big_ugroove_small_r / 2, 0]), Rz(180 + 90)),
    'b': chain(T([-_push * math.cos(math.radians(60)), -71 + _push * math.sin(math.radians(60)), 0]),
               Rz(180), T([104, 0, 0]), Rz(180)),
    'c': chain(T([104 + _push * math.cos(math.radians(60)),
                  -71 + _push * math.sin(math.radians(60)), 0])),
}

# `top_plate()`
PLATE = chain(T([-cx / 2, Yshift_top_plate, -12]))
PLATE_SIZE = (cx, cy, 12)

# `odrive()`
ODRIVES = [chain(T([188, -208.4, 0]), Rz(180)), chain(T([-48, -208.4, 0]), Rz(180))]
ODRIVE_SIZE = (140, 50, 2)
ODRIVE_HOLES = [(140 - 2.5, 50 - 2.5), (2.5, 50 - 2.5), (140 - 2.5, 4), (2.5, 4)]
ODRIVE_HOLE_DIAMETER = 3


def internal_lines(sidelength):
    """`ceiling_unit_internal_lines_v4p1()`: the segments, as (start,
    end) pairs in the ceiling-lines frame, grouped by winch, in the
    order the layout draws them.  The first segment of each winch's
    first group leaves its spool."""
    lines = {A: [], B: [], C: [], D: []}

    def one_b_line(mirror, offset, e=0.0):
        a = -bc_x_pos - spd / 2
        b = bcspool_y + move_BC_deflectors + e
        c = math.cos(math.radians(60)) * b623_big_ugroove_small_r
        d = math.sin(math.radians(60)) * b623_big_ugroove_small_r
        m = -1.0 if mirror else 1.0
        return [
            ((m * (a + offset), bcspool_y, hz), (m * (a + offset - 0.5), b + 10, hz)),
            ((m * (a + offset - c + 0.5), b + d - 0.7, hz + 2),
             (m * (a + offset - c - math.cos(math.radians(30)) * 100),
              b + d - math.sin(math.radians(30)) * 100, hz + 150)),
        ]

    for k, winch in ((0, C), (1, B)):
        lines[winch] += one_b_line(k == 1, 0)
        lines[winch] += one_b_line(k == 1, spd)

    yv = sidelength / math.sqrt(12) + Move_d_bearings_inwards / 2 - b623_width / 2 - 1
    lines[D] += [
        ((lx0, bcspool_y, hz), (lx0, yv, hz)),
        ((lx0, yv, hz), (-sidelength / 2, yv, hz)),
        ((lx1, bcspool_y, hz), (lx1, yv, hz)),
        ((lx1, yv, hz), (sidelength / 2, yv, hz)),
        ((lx2, bcspool_y, hz), (lx2, ly2(sidelength), hz)),
        ((lx2, ly2(sidelength), hz), (b623_width / 2 + 1, ly2(sidelength), hz)),
        ((b623_width / 2 + 1, ly2(sidelength), hz),
         (b623_width / 2 + 1, -sidelength / math.sqrt(3) - Move_d_bearings_inwards, hz)),
    ]

    for k in (0, spd):
        ydiff = 0
        lines[A] += [
            ((lx3 + k, aspool_y, hz), (lx3 + k, ydiff + aspool_y - aspool_lineroller_y + 7, hz)),
            ((lx3 + k, ydiff + aspool_y - aspool_lineroller_y + 7, hz),
             (lx3 + k + (k - spd / 2), ydiff + aspool_y + 190, 100 + hz)),
        ]
    return lines


def stubs(sidelength):
    """The far ends of the segments that leave the ceiling toward the
    anchors -- the layout's 100 to 150 mm stubs -- in the machine frame,
    per ABC winch, with the direction they head."""
    result = {}
    for winch in (A, B, C):
        result[winch] = []
        segments = internal_lines(sidelength)[winch]
        for start, end in segments[1::2]:
            p0, p1 = apply(CEILING_LINES, start), apply(CEILING_LINES, end)
            result[winch].append((p1, (p1 - p0) / numpy.linalg.norm(p1 - p0)))
    return result


def spool_exit(winch, sidelength):
    """Where the winch's first line leaves its spool, and which way, in
    the winch's own frame."""
    start, end = internal_lines(sidelength)[winch][0]
    to_winch = numpy.linalg.inv(chain(CEILING, WINCH_STATIONS[winch])) @ CEILING_LINES
    p0, p1 = apply(to_winch, start), apply(to_winch, end)
    return p0, (p1 - p0) / numpy.linalg.norm(p1 - p0)


# --- layout.scad: the mover ---------------------------------------------------

CORNERS = (0, 120, 240)
MOVER_LIFT = (0, 0, length_of_toolhead)


def corner_frame(k):
    """`rotate([180, 0, k + 180])`, for corner `k` in degrees."""
    return R([180, 0, k + 180])


def beam(k, sidelength, beam_length):
    return chain(corner_frame(k),
                 T([-beam_length / 2, -(sidelength + 10.5) / math.sqrt(12) - math.sqrt(3), 0]))


MARKER_D = 32
MARKER_DIAMETER = 90
MARKER_OFFSETS = {0: (0, 26), 120: (-21, 78), 240: (-50, 76)}   # constant, per-side slope


def markers(k, sidelength, beam_length):
    """The two hp-mark markers on beam `k`: their frames, disc down."""
    marker_shift = beam_length / 3
    base, slope = MARKER_OFFSETS[k]
    return [chain(beam(k, sidelength, beam_length),
                  T([marker_shift + l * (-marker_shift * 2 + beam_length), Beam_width / 2, 2]),
                  T([0, 0, -MARKER_D / 2 + 7]),
                  T([base + slope * l, 0, 0]))
            for l in (0, 1)]


MARKER_POST = chain(T([-5, -10, 4]))
MARKER_POST_SIZE = (10, 20, 20)
MARKER_PIN = chain(T([0, 0, 1]))
MARKER_PIN_DIAMETER, MARKER_PIN_HEIGHT = 3, 8


def corner_clamp(k, sidelength):
    return chain(corner_frame(k),
                 T([0, sidelength / math.sqrt(3) - Cc_action_point_from_mid, -Wall_th]))


RAM = chain(T([0, 0, -ram_1000_3dpotter_height_diff - 76]))
RAM_HOLDER = chain(T([0, 0, -364]))
RAM_TOP_HOLDER = chain(T([0, 0, 322]))

sidelength_frac = 1.5
offcenter_frac = 25


def shorter_beam(sidelength):
    return sidelength / sidelength_frac


def short_beam(sidelength):
    return chain(T([-shorter_beam(sidelength) / 2, sidelength / offcenter_frac, 0]))


def extruder_holder(sidelength):
    return chain(short_beam(sidelength), R([90, 0, 90]),
                 T([-2 * Wall_th, 0,
                    shorter_beam(sidelength) / 2 - (Nema17_cube_width + 0.54 * 2 + 2 * Wall_th) / 2]))


HOTEND = chain(T([0, 0, -length_of_toolhead + 10]))
HOTEND_DIAMETER = 10
DRIVE_BOX = chain(T([-20, -15, -40]))
DRIVE_BOX_SIZE = (40, 25, 40)


def mover_corner_point(k, sidelength):
    """Where the D line attaches at corner `k`, relative to the mover."""
    return numpy.array(rotation2((0, sidelength / math.sqrt(3), 0), -k)) + MOVER_LIFT


# --- layout.scad: the anchors and the lines --------------------------------------

Ext_sidelength = 500
ANCHOR_PLATE_SIZE = (50, Ext_sidelength, 8)
ANCHOR_PLATE = chain(T([0, -Ext_sidelength / 2, -8]))
ANCHOR_TOWERS = [
    chain(T([26, Ext_sidelength / 2 - 27.91, 0]), Rz(-90)),
    chain(M([0, 1, 0]), T([26, Ext_sidelength / 2 - 27.91, 0]), Rz(-90)),
]


def anchor_frame(i, sidelength):
    """`ABC_anchors()`: where anchor `i`'s `ABC_anchor()` stands."""
    return chain(T(anchors[i]), Rz(i * 120),
                 T([0, -sidelength / math.sqrt(8) + 5, length_of_toolhead - 50]), Rz(-90))


def action_points(sidelength):
    """The four line offsets of an anchor, before its rotation, in the
    layout's order: high left, low left, high right, low right."""
    high_left = numpy.array([-sidelength / 2, -sidelength / math.sqrt(8) + 5,
                             length_of_toolhead - 2])
    low_left = high_left - [0, 0, Corner_clamp_bearings_center_to_center + 2 * b623_big_ugroove_big_r]
    high_right = high_left + [sidelength, 0, 0]
    low_right = low_left + [sidelength, 0, 0]
    return [high_left, low_left, high_right, low_right]


ACTION_NAMES = ('high_left', 'low_left', 'high_right', 'low_right')


def anchor_segments(i, sidelength):
    """Anchor `i`'s four segments as (anchor end, mover offset): the
    mover end is `pos + offset`."""
    return [(anchors[i] + rotation2(p, i * 120), rotation2(p, i * 120))
            for p in action_points(sidelength)]


def d_segments(sidelength):
    """The three D lines as (ceiling end, mover offset)."""
    r = sidelength / math.sqrt(3)
    offsets = [
        (0, r, 0),
        (math.cos(math.radians(30)) * r, -math.sin(math.radians(30)) * r, 0),
        (-math.cos(math.radians(30)) * r, -math.sin(math.radians(30)) * r, 0),
    ]
    return [(anchors[D] + numpy.array(o), numpy.array(o) + MOVER_LIFT) for o in offsets]


LINE_RADIUS = 1.0

#: Segments each winch's line makes to the mover: how much line a spool
#: pays out per millimetre of anchor distance.
ADVANTAGE = {A: 2, B: 2, C: 2, D: 1}


def line_length(i, pos):
    """The layout's segment length for anchor `i` at mover `pos`."""
    pos = numpy.asarray(pos, dtype=float)
    if i == D:
        return float(numpy.linalg.norm(anchors[D] - pos - MOVER_LIFT))
    return float(numpy.linalg.norm(anchors[i] - pos))
