"""Part colours: the layout's own where it gives one, a material's
where it does not.

A node's colour is a property of the node, so every leaf carries one
colour.  The layout colours in RGBA with the alpha dropped here; the
viewer draws solids.
"""


def _rgb(r, g, b):
    return '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))


# the layout's palette
PLATE = 'sandybrown'.replace('sandybrown', '#f4a460')       # color0
PRINTED = _rgb(0.81, 0.73, 0.05)                            # color1: the printed parts
SPOOL_GEAR = _rgb(0.99, 0.99, 0.99)                         # color2
CARBON = _rgb(0.2, 0.2, 0.2)                                # color_carbon
LINE = '#008000'                                            # color_line: "green"
MOVER_LINE = '#ffc0cb'                                      # the anchor and D lines: "pink"
MOTOR = _rgb(0.5, 0.4, 0.9)
MOTOR_GEAR = _rgb(0.75, 0.75, 0.75)
BELT = _rgb(0.3, 0.3, 0.3)
SMOOTH_ROD = '#808080'                                      # "grey"
ODRIVE = _rgb(0.1, 0.1, 0.1)
BED = _rgb(0.7, 0.2, 0.2)
MARKER = _rgb(0.9, 0.9, 0.9)
HOLDER = _rgb(0.2, 0.2, 0.2)                                # the clay extruder's holders
HOTEND = '#ff0000'                                          # "red"
DRIVE_BOX = _rgb(0.1, 0.1, 0.1)

# what the layout leaves uncoloured
BEARING = '#8c8c8c'                                         # the 623 belt rollers: steel
ANCHOR_PLATE = '#c8a878'                                    # the anchors' plywood
CLAY_EXTRUDER = '#e6e6e6'                                   # the ram extruder's tube (its module's own 0.9 grey)
ENCODER = '#2a6e3f'                                         # the motor's encoder board
