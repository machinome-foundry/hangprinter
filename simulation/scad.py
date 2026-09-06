"""Access to Torbjørn's OpenSCAD design, which lives in `src/` beside
this package, with its exported parts in `stl/`.

This package does not replace the design; it reads it.  A part the
layout imports as an STL is that file; a part it calls as a module is
reached through solid2's ``import_scad``, which emits ``use <absolute
path>`` so the design's relative ``include <lib/parameters.scad>``,
``use <lib/util.scad>`` and ``import("../stl/...")`` keep resolving
from the source directory.  ``OpenScadNode`` is deliberately not used:
it inlines the .scad text into the generated file under ``_build``,
where none of those relative references resolve.

`src/layout.scad` itself cannot be imported this way -- solid2's parser
refuses the `data_collection_positions_standard` table on its line 808
-- so its placements are restated in `layout.py`.
"""

import os

from solid2 import import_scad

SOURCE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SRC = os.path.join(SOURCE_DIR, 'src')
STL = os.path.join(SOURCE_DIR, 'stl')


def _handle(filename):
    return import_scad(os.path.join(SRC, filename))


util = _handle('lib/util.scad')
landing_brackets = _handle('landing_brackets.scad')
line_roller_anchor = _handle('line_roller_anchor.scad')
ram_holder = _handle('ram_1000_3dpotter_holder.scad')
ram_top_holder = _handle('ram_1000_3dpotter_top_holder.scad')


def scad_sources():
    """Every OpenSCAD source and mesh the design is built from.

    The whole tree rather than a per-node closure: OpenSCAD's own
    ``include``/``use``/``import`` graph is not visible to the framework's
    Python import walk, and an unnecessary rebuild is cheaper than stale
    geometry.
    """
    files = set()
    for base in (SRC, STL):
        for root, _, names in os.walk(base):
            files.update(os.path.join(root, name) for name in names
                         if name.endswith(('.scad', '.stl')))
    return files
