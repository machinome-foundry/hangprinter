"""The mover: `mover()`, in its own frame -- the nozzle tip on the
origin, the corner triangle `length_of_toolhead` above it.

Three carbon beams with their hp-mark markers, a corner clamp at each
vertex, and the toolhead: the clay extruder the layout renders by
default, or, with `clay` off, the shorter beam with the extruder holder,
the hot end and the drive box its `else` branch draws.
"""

from solid2 import cube, cylinder
from machinome.motion.joints import Prismatic
from machinome.node.assembly import AssemblyNode
from machinome.node.solid2 import Solid2Node
from machinome.parameters import Flag, Length

from simulation import layout, materials
from simulation.frames import T, chain
from simulation.layout import (
    CORNERS,
    DRIVE_BOX, DRIVE_BOX_SIZE,
    HOTEND, HOTEND_DIAMETER,
    MARKER_D, MARKER_DIAMETER, MARKER_PIN_DIAMETER, MARKER_PIN_HEIGHT, MARKER_POST_SIZE,
    RAM, RAM_HOLDER, RAM_TOP_HOLDER,
    Beam_width,
    Cc_plastic_length,
    length_of_toolhead,
    sidelength_frac,
)
from simulation.part import Box, DesignStl, Rod, ScadPart, place
from simulation.scad import ram_holder, ram_top_holder


class Beam(Box):
    color = materials.CARBON


#: How far the marker's pin is drawn under its hole in the clip, and
#: the clip's pocket over the beam it goes round: clearances so the
#: pairs can be asked whether they touch.
PIN_CLEARANCE = 0.05
CLIP_CLEARANCE = 0.05


class Marker(Solid2Node):
    """An hp-mark marker: the layout's 90 mm disc with the 3 mm pin
    through its centre, one part.  The layout draws the pin as a piece
    of its own overlapping the disc and the clip; it is the disc's."""
    color = materials.MARKER
    fn = 96

    def render(self):
        disc = cylinder(d=MARKER_DIAMETER, h=1)
        pin = (cylinder(d=MARKER_PIN_DIAMETER, h=MARKER_PIN_HEIGHT, _fn=24)
               .translate([0, 0, 1 - MARKER_PIN_HEIGHT / 2]))
        return disc + pin


class MarkerClip(Solid2Node):
    """The layout's marker block, `cube([10, 20, 20])` at `[-5, -10, 4]`
    in the marker's frame, which it draws straight through the beam and
    around the pin.  A clip goes *around* a beam: the beam's own section
    is taken out of it, and the pin's hole with it.  Its outer bounds
    are the layout's."""
    color = materials.CARBON

    #: The beam's section in the marker's frame: the marker sits 2 mm
    #: over the beam's top face and 7 mm inside its centre line.
    BEAM_TOP = MARKER_D / 2 - 7 - 2
    BEAM_BOTTOM = BEAM_TOP + Beam_width

    def render(self):
        block = cube(list(MARKER_POST_SIZE)).translate([-5, -10, 4])
        beam = (cube([MARKER_POST_SIZE[0] + 2, Beam_width + 2 * CLIP_CLEARANCE,
                      Beam_width + 2 * CLIP_CLEARANCE])
                .translate([-6, -Beam_width / 2 - CLIP_CLEARANCE, self.BEAM_TOP - CLIP_CLEARANCE]))
        hole = (cylinder(d=MARKER_PIN_DIAMETER + 2 * PIN_CLEARANCE,
                         h=MARKER_PIN_HEIGHT, _fn=24)
                .translate([0, 0, 1 - MARKER_PIN_HEIGHT / 2]))
        return block - beam - hole


class CornerClamp(DesignStl):
    stl_source = '../stl/corner_clamp.stl'


class ClayExtruder(DesignStl):
    """The 3D Potter ram extruder's tube, motor and drive, as rendered
    for the layout; the file's nozzle body is `ClayNozzle`, and its four
    inside-out shells (the NEMA 23 screw holes) are nobody's."""
    stl_source = '../stl/for_render/ram_1000_3dpotter.stl'
    body = 4
    color = materials.CLAY_EXTRUDER


class ClayNozzle(DesignStl):
    stl_source = '../stl/for_render/ram_1000_3dpotter.stl'
    body = 5
    color = materials.HOLDER


class RamHolder(ScadPart):
    color = materials.HOLDER

    def render(self):
        return ram_holder.ram_1000_3dpotter_holder()


class RamTopHolder(ScadPart):
    color = materials.HOLDER

    def render(self):
        return ram_top_holder.ram_1000_3dpotter_top_holder()


class ExtruderHolder(DesignStl):
    """`extruder_holder.stl` is a print pack: the holder with three cable
    clampers laid out beside it.  The holder is the part."""
    stl_source = '../stl/extruder_holder.stl'
    body = 3


class Hotend(Solid2Node):
    """The layout's stand-in hot end: a 10 mm barrel the length of the
    toolhead on a cone down to the tip."""
    color = materials.HOTEND
    fn = 48

    def render(self):
        return (cylinder(d=HOTEND_DIAMETER, h=length_of_toolhead)
                + cylinder(d1=1, d2=HOTEND_DIAMETER, h=10).translate([0, 0, -10]))


class DriveBox(Solid2Node):
    """The layout's stand-in extruder drive: a 40 x 25 x 40 block over
    the hot end, which the layout draws straight through it.  The block
    gets a bore for the hot end's barrel, at the pin's clearance."""
    color = materials.DRIVE_BOX
    fn = 48

    def render(self):
        block = cube(list(DRIVE_BOX_SIZE))
        bore = (cylinder(d=HOTEND_DIAMETER + 2 * PIN_CLEARANCE, h=DRIVE_BOX_SIZE[2] + 2)
                .translate([-DRIVE_BOX[0][3], -DRIVE_BOX[1][3], -1]))
        return block - bore


class Mover(AssemblyNode):

    beam_length = Length(layout.Beam_length, min=0)
    clay = Flag(True)

    #: The mover's three freedoms against the ceiling: `Hangprinter.render()`
    #: never places this node, so the parent frame is the machine frame and
    #: these axes are the machine's own -- exactly the frame
    #: `Hangprinter.simulate()` used to translate in by hand. No `range`:
    #: the drivers already carry the sliders' presentation range.
    travel_x = Prismatic(axis=(1, 0, 0), unit='mm')
    travel_y = Prismatic(axis=(0, 1, 0), unit='mm')
    travel_z = Prismatic(axis=(0, 0, 1), unit='mm')

    sidelength = beam_length + Length(2 * Cc_plastic_length)
    shorter_beam = sidelength / sidelength_frac

    beams = Beam(x=beam_length, y=Beam_width, z=Beam_width).repeat(3)
    markers = Marker().repeat(6)
    marker_clips = MarkerClip().repeat(6)
    clamps = CornerClamp().repeat(3)

    extruder = ClayExtruder()
    nozzle = ClayNozzle()
    holder = RamHolder()
    top_holder = RamTopHolder()

    short_beam = Beam(x=shorter_beam, y=Beam_width, z=Beam_width)
    extruder_holder = ExtruderHolder()
    hotend = Hotend()
    drive_box = DriveBox()

    def render(self):
        lift = T(layout.MOVER_LIFT)
        sidelength, beam_length = self.sidelength, self.beam_length
        markers = iter(zip(self.markers, self.marker_clips))
        for k, beam, clamp in zip(CORNERS, self.beams, self.clamps):
            place(beam, chain(lift, layout.beam(k, sidelength, beam_length)))
            for frame in layout.markers(k, sidelength, beam_length):
                marker, clip = next(markers)
                place(marker, chain(lift, frame))
                place(clip, chain(lift, frame))
            place(clamp, chain(lift, layout.corner_clamp(k, sidelength)))

        if self.clay:
            for node in (self.short_beam, self.extruder_holder, self.hotend, self.drive_box):
                node.omit()
            place(self.extruder, chain(lift, RAM))
            place(self.nozzle, chain(lift, RAM))
            place(self.holder, chain(lift, RAM_HOLDER))
            place(self.top_holder, chain(lift, RAM_TOP_HOLDER))
        else:
            for node in (self.extruder, self.nozzle, self.holder, self.top_holder):
                node.omit()
            place(self.short_beam, chain(lift, layout.short_beam(sidelength)))
            place(self.extruder_holder, chain(lift, layout.extruder_holder(sidelength)))
            place(self.hotend, chain(lift, HOTEND))
            place(self.drive_box, chain(lift, DRIVE_BOX))
