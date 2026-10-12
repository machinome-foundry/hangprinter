"""The GT2 timing belt the four winches run, and what a pulley that
meshes on it has to be.

Carried over from the Kossel's `gt2.py`, itself from Metamaquina 2's
(same author, same workspace), where these restatements of molejo's
wrap rule and tooth form were first worked out against a real machine.
Nothing here is Hangprinter-specific: it is what GT2 *is*.  What the
winches' loops run on -- which circles, how wide -- arrives as arguments
from `belt`.

molejo authors a belt as a `Wrap`: an ordered list of circles in the XY
plane, run along their external tangents, clockwise seen from +Z, with
the belt's width along +Z and the swept path being the belt's *pitch
line*.  The circles a wrap takes are pitch circles, so a contact radius
is converted differently for a toothed pulley (`on_pulley`) and a plain
bearing the tooth tips ride (`on_idler`); a clamp is anchored at a
distance *along* a tangent span, which `span_origin` and `span_scale`
convert a carriage position to; and a pulley's groove is the shape of
everything a tooth does on its way in and out (`groove`), cut from
molejo's own tooth form (`modulation`).
"""

import math

import numpy
from molejo import Polygon, Teeth
from machinome.node.molejo import MolejoNode
from machinome.mechanics import belt_path_metrics, pulley_pitch_radius

from simulation import materials
from simulation.scad import scad_sources


#: The pitch of GT2, and what the standard is named after.
PITCH = 2.0

#: How far a tooth stands proud of the land between two teeth.
TOOTH_HEIGHT = 0.75

#: The belt's whole section, back and tooth together.
THICKNESS = 1.38

#: The pitch line differential: how far the pitch line -- the neutral
#: line a belt's length is measured along, and the line molejo sweeps
#: the section along -- lies outside the land between two teeth.  It is
#: what makes a 20 tooth pulley 12.32 mm across the flanks and 12.73 mm
#: across the pitch circle.
PITCH_LINE = 0.254

#: The back of the belt, from the pitch line outwards.
BACK = THICKNESS - TOOTH_HEIGHT - PITCH_LINE

#: How many rings molejo spends on each element of a loop.
#:
#: A wrap's tessellation is per element and a wrap has two elements per
#: circle -- one tangent span and one arc -- so every element gets this
#: many rings whether it is the 375 mm run down the X beam or the 19 mm
#: of arc at the end of it.  The long run is what sets the number: it
#: carries around 190 teeth, and a trapezoid needs several samples
#: across to read as a trapezoid rather than as noise.  A thousand is
#: the compromise this design is drawn at -- five or six rings a tooth
#: on the longest element, generous everywhere else -- and it is a
#: sampling instruction only: the exact solid and the loop's own
#: measurements are analytic and do not depend on it.
PATH_SAMPLES = 1024


def section(width, face='inner'):
    """The belt's cross-section, as molejo takes it.

    In a wrap's profile frame local x is the outward normal and local y
    is the world +Z the belt's width runs along, so this is the belt
    seen end-on.  The points run counter-clockwise, which is molejo's
    winding, and the two on the face named by `face` are the ones `Teeth`
    displaces.

    A belt has teeth on one face and which one is the loop's business
    rather than the section's.  The X loop is driven from inside its own
    circuit, so its teeth are on the inner face, at the minimum x; the Y
    loop is driven from outside it, over a reverse bend, so its teeth are
    on the outer face and its smooth back is what rides the three
    bearings.  Either way the belt is `THICKNESS` thick and the pitch
    line sits `PITCH_LINE` in from the toothed side of it; all that moves
    is which side that is.

    The width runs from nought to `width` rather than either side of
    nought, so that a node placing this loop places it exactly where the
    design's own ``linear_extrude(belt_width)`` put its hulled ring.
    """
    if face == 'outer':
        inner, outer = -BACK, PITCH_LINE
    else:
        inner, outer = -PITCH_LINE, BACK
    return Polygon([
        (inner, 0.0),
        (outer, 0.0),
        (outer, width),
        (inner, width),
    ])


def on_pulley(centre, radius, turn='clockwise'):
    """The pitch circle of a belt meshed on a toothed pulley.

    The pulley's teeth stand in the gaps between the belt's, so what
    touches the pulley's flank circle is the land between two teeth, and
    the pitch line is one pitch line differential outside it.  That is
    true of a pulley inside the loop and of one the belt is bent
    backwards over alike -- the belt is the same distance from the metal
    either way -- so `turn` changes only which side of the belt is
    against it, and molejo is what is told about that.
    """
    circle = {'center': [centre[0], centre[1]], 'radius': radius + PITCH_LINE}
    if turn != 'clockwise':
        circle['turn'] = turn
    return circle


def on_idler(centre, radius, face='inner'):
    """The pitch circle of a belt running on a plain bearing.

    Every idler in both machines is a 608 bearing with nothing to mesh
    with, so what it carries is whichever face of the belt happens to be
    against it.  A belt with its teeth inward rides on its tooth *tips*,
    a whole tooth out from where it would sit on a pulley; a belt with
    its teeth outward presents its smooth back instead, which is only
    `BACK` out.  The two put the belt's material in exactly the same
    band -- it is `THICKNESS` thick and its inner face is on the race
    either way -- and move only the pitch line inside it.
    """
    reach = BACK if face == 'outer' else TOOTH_HEIGHT + PITCH_LINE
    return {'center': [centre[0], centre[1]], 'radius': radius + reach}


def pulley_teeth(radius):
    """How many teeth a pulley whose flanks stand at `radius` carries.

    `tooth_count` read the other way, for a circle instead of a loop: a
    pulley's flank circle is one pitch line differential inside the
    pitch circle the belt runs on, and that circle carries a whole
    number of nominal pitches.  A design that writes a pulley down as a
    radius rather than as a tooth count -- as this one does, in
    `PulleyRadius` -- has named it by a number that can name no pulley
    at all, and this says which one it did name.  That is how the round
    6 was caught, and it is how the number that replaced it is checked
    against the pulley the bill of materials buys.
    """
    return round(2 * math.pi * (radius + PITCH_LINE) / PITCH)


def pulley_radius(teeth, period=PITCH):
    """Where the flanks of a pulley of `teeth` teeth stand.

    `period` is the pitch its grooves are really spaced at, which for a
    pulley meshed with a drawn loop is the loop's own `pitch` and not
    the nominal `PITCH` a catalogue pulley is cut at: molejo divides a
    loop's length by a whole tooth count rather than stepping 2 mm
    around it, so a drawn loop comes out a fortieth of a percent off
    the standard.  On the machine that difference is taken up in belt
    tension.  In a drawing there is no tension to take it up with, so
    the pulley is cut to the belt it drives instead.
    """
    return pulley_pitch_radius(teeth, period) - PITCH_LINE


def modulation(fraction):
    """How much tooth stands at `fraction` of the way through one
    period: nought on the land between two teeth, one at a crest.

    molejo's own tooth form, restated -- a quarter crest centred on the
    pattern origin, a quarter ramp, a quarter root and a quarter ramp
    back.  molejo publishes it only as the mesh it displaces, and a
    pulley the belt meshes on is exactly this curve read as a solid's
    boundary rather than as an offset, so the two cannot be allowed to
    disagree.
    """
    fraction %= 1.0
    away = min(fraction, 1.0 - fraction)
    return max(0.0, min(1.0, (0.375 - away) * 4.0))


#: How finely a tooth's way out of its groove is followed.
#:
#: The sampling is square: this many stations across one tooth, and
#: this many advances for each of them, so a millionth of a tooth's
#: passage is looked at.  It is deliberately far finer than the outline
#: it feeds, which takes the deepest of a whole step at a time -- a
#: missed sample can only ever leave a groove tighter than it should be,
#: and the step is where that is made safe rather than here.
PASSAGE_SAMPLES = 1024

#: How far past the pitch circle a tooth is followed, in teeth.
#:
#: A crest sits 1.004 mm inside the pitch line, so it has cleared the
#: flank circle once it is 2.93 mm along the straight run -- a tooth and
#: a half.  Three is that with room, and the sampling stops early
#: anyway: `_passage` drops every station the moment its tooth is out.
PASSAGE_REACH = 3


def _passage(teeth, period, bins):
    """The deepest a tooth reaches into a pulley, by angle, on its way
    out of the groove it was seated in.

    A belt leaves a pulley along a tangent, so in the pulley's own frame
    a tooth on the way out is a tooth on a straight line rolling off a
    circle: it lifts out of its groove while the pulley turns under it,
    and it sweeps.  Everything here follows from that one picture.  A
    tooth seated at station `m` sits at pulley angle `m / pitch radius`
    and stays there; once it is `run` past the tangent point it stands
    at `hypot(seat, run)` from the centre, at an angle the pulley's own
    turn has carried a further `run / pitch radius` on and the tangent
    has swung `atan2(run, seat)` back.

    A groove is cut once and every tooth goes through it, so the answer
    is the deepest reach at each angle over the whole passage.  Coming
    on is going off with time reversed, which is a reflection, so the
    two halves are folded together at the end rather than derived
    twice.
    """
    pitch_radius = pulley_pitch_radius(teeth, period)
    flank = pitch_radius - PITCH_LINE

    station = numpy.linspace(0.0, period, PASSAGE_SAMPLES, endpoint=False)
    seat = pitch_radius - numpy.array(
        [PITCH_LINE + TOOTH_HEIGHT * modulation(place / period)
         for place in station])
    run = numpy.linspace(0.0, PASSAGE_REACH * period, PASSAGE_SAMPLES)[1:]

    radius = numpy.hypot(seat[:, None], run[None, :])
    angle = (station[:, None] / pitch_radius
             + run[None, :] / pitch_radius
             - numpy.arctan2(run[None, :], seat[:, None]))

    biting = radius < flank
    tooth = 2 * math.pi / teeth
    index = ((angle % tooth) / tooth * bins).astype(int) % bins

    deepest = numpy.zeros(bins)
    numpy.maximum.at(deepest, index[biting], (flank - radius)[biting])
    return numpy.maximum(deepest, deepest[(-numpy.arange(bins)) % bins])


def groove(teeth, period, steps, fine=16):
    """How deep a pulley's groove is at each of `steps` points through
    one tooth.

    Not the tooth's own shape.  A tooth is a trapezoid and a trapezoid
    cannot get out of a trapezoid: seat one exactly and it is trapped,
    because leaving means swinging about the tangent point and the
    corners have nowhere to swing to.  Drawn as the exact negative the
    pulley bites its own belt at the two places where a tooth is
    halfway in or halfway out -- two tenths of a cubic millimetre of
    it, at the two ends of the wrap and nowhere else, which is what
    sent this function looking.  So a groove is not the shape of a
    tooth; it is the shape of everything the tooth does on its way
    through, and the floor and the flat between two grooves come out
    untouched while the flanks are scooped back by up to 0.17 mm.
    That is what a real timing pulley's curved grooves are for.

    Each returned point is the deepest reach anywhere within one step
    either side of it, because a chord of the polygon this feeds stands
    as far out as its outer end: a tooth passing between two points has
    to clear both of them.  The over-cut that follows is flank
    clearance, which is a thing a pulley has and a drawing usually
    forgets, and it leaves the two surfaces that actually carry -- the
    groove floor and the land between grooves -- exactly where they
    were.
    """
    bins = steps * fine
    needed = numpy.maximum(
        _passage(teeth, period, bins),
        [TOOTH_HEIGHT * modulation(index / bins) for index in range(bins)])
    return [max(needed[(step * fine + offset) % bins]
                for offset in range(-fine, fine + 1))
            for step in range(steps)]


def tooth_count(circles):
    """How many teeth the loop through `circles` carries.

    molejo takes the count as a declaration rather than deriving it,
    because a count that followed a parameter would change the vertex
    count with it.  So it is derived once, here, from the loop the
    geometry gives: the nearest whole number of nominal pitches around
    it.  A belt is bought by tooth count and tensioned to fit, which is
    the same arithmetic run the other way.
    """
    return round(length(circles) / PITCH)


def pitch(circles):
    """The pitch the teeth of the loop through `circles` are drawn at.

    Not quite `PITCH`.  molejo divides the loop by the declared tooth
    count rather than stepping a nominal pitch around it, because a
    whole number of teeth is what closes the pattern at the seam and
    what keeps a moving idler changing the pitch rather than the count.
    A real belt does the same thing with its own tension.
    """
    return length(circles) / tooth_count(circles)


def teeth(circles, face='inner'):
    """The tooth pattern of a GT2 belt run around `circles`."""
    return Teeth(pitch=PITCH, height=TOOTH_HEIGHT, flank='trapezoid',
                 count=tooth_count(circles), face=face)


def length(circles):
    """The pitch length of the loop through `circles`.

    What a catalogue calls the belt's length, and what molejo divides by
    the tooth count to get the pitch it actually draws at.
    """
    return _metrics(circles)['length']


def span_origin(circles, span):
    """Where tangent span `span` of the loop begins, in the wrap's plane.

    The wrap's arc-length origin is where the belt leaves the first
    circle, and an anchor is measured from the start of the span it
    names, so this is the point a clamp's position is measured from.
    """
    return spans(circles)[span][0]


def span_scale(circles, span):
    """Millimetres of belt per millimetre of travel along tangent span
    `span`, for a carriage running along the wrap plane's x.

    An anchor is a distance along the span; a carriage is at a position
    along the machine's axis.  The two differ by the span's tilt, which
    is nought only when the two circles the span joins have the same
    radius -- as the Y belt's three do, and the X belt's pulley and
    idler do not.  On the X belt it comes to two parts in a million,
    well under a micron across the travel, so this is a correctness
    matter rather than a visible one.  It is written down because the
    conversion is real, not because the number is large.
    """
    return 1.0 / spans(circles)[span][1][0]


def spans(circles):
    """The loop's tangent spans, each as (start, direction, length).

    molejo's rule, restated: for consecutive circles at distance *L*
    with radii *r* and *r'*, each signed by which way the belt turns
    about it, the normal both are touched along is
    ``n = d*u + sqrt(1 - d*d)*rot90(u)`` for ``d = (r - r')/L`` and ``u``
    the unit vector between the centres, and the belt runs from one
    tangent point to the next in the direction ``(n_y, -n_x)``.  Where
    the two senses agree that is the external tangent; where they differ
    it is the internal one, which crosses between the centres.
    """
    return list(_metrics(circles)['spans'])


def stations(circles):
    """Where each of the loop's 2k elements begins, in belt.

    Span 0, the arc about circle 1, span 1, ... and finally the arc
    about circle 0, which is molejo's own ordering: the loop's origin is
    where the belt leaves the first circle.  An anchor is measured from
    the start of a span and a pulley's phase from the start of its own
    arc, so converting between the two needs to know where both of them
    begin.
    """
    return list(_metrics(circles)['stations'])


def _sense(circle):
    """Which way the belt turns about `circle`: ``-1`` where the loop is
    concave, because the belt is bent backwards over it."""
    return -1.0 if circle.get('turn') == 'counterclockwise' else 1.0


def _arcs(circles):
    """How much belt is wrapped around each circle, in order.

    The belt arrives on the normal of the span before a circle and
    leaves on the normal of the span after it, and turns between the two
    the way that circle's sense says.  What it arrives at is the point a
    radius along that normal or a radius against it, so the angles are
    taken from the signed normal rather than the normal itself.
    """
    arcs = _metrics(circles)['arc_lengths']
    return list(arcs[1:] + arcs[:1])


def _metrics(circles):
    """Shared path measurements adapted from this module's circle records."""
    return belt_path_metrics(
        tuple(circle['center'] for circle in circles),
        tuple(circle['radius'] for circle in circles),
        tuple(_sense(circle) for circle in circles))


class Belt(MolejoNode):
    """A GT2 belt of this machine, as a flexible leaf.

    Shares with `ScadPart` the thing every part in this package shares
    -- its dimensions are read from the .scad sources, which no Python
    import mentions, so an edit there has to invalidate it -- but not
    its geometry, which is molejo's rather than an OpenSCAD module's.

    A subclass declares one port per shape parameter and returns the
    shape; the axis that owns it connects the port.  Both belts here
    have exactly one parameter, the clamp their ends are held by.
    """

    color = materials.BELT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = self.files | scad_sources()
