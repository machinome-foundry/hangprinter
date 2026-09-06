"""The design's own answer to where everything is: its CSG export.

`openscad -o layout.csg src/layout.scad` writes the layout's tree as
`multmatrix`, `import`, `cube` and `cylinder` nodes with every transform
composed, without evaluating any geometry, in a tenth of a second.  The
tests read that tree to check the placements this package restates in
Python against the design that states them.  `-D` overrides the layout's
mover position table, so the design can be asked for any pose.

This module defines no node and is imported only by tests.
"""

import ast
import os
import re
import subprocess
import tempfile

import numpy

from simulation.scad import SOURCE_DIR

LAYOUT = os.path.join(SOURCE_DIR, 'src', 'layout.scad')

_HEAD = re.compile(r'\s*([A-Za-z_][A-Za-z_0-9]*)\s*\(')


class Leaf:
    """One primitive of the design with its composed transform."""

    def __init__(self, kind, params, matrix, color, subtracted):
        self.kind = kind
        self.params = params
        self.matrix = matrix
        self.color = color
        self.subtracted = subtracted

    @property
    def file(self):
        """An import's file, relative to the design's `src/`."""
        return self.params.get('file')

    def point(self, local):
        """A local point in world coordinates."""
        return (self.matrix @ numpy.array([*local, 1.0]))[:3]

    def cylinder_ends(self):
        """A cylinder's two end centres in world coordinates."""
        height = self.params['h']
        z0 = -height / 2 if self.params.get('center') else 0.0
        return self.point((0, 0, z0)), self.point((0, 0, z0 + height))

    def cube_bounds(self):
        """A cube's eight corners in world coordinates, as bounds."""
        size = self.params['size']
        origin = [-s / 2 for s in size] if self.params.get('center') else [0, 0, 0]
        corners = [self.point((origin[0] + i * size[0], origin[1] + j * size[1],
                               origin[2] + k * size[2]))
                   for i in (0, 1) for j in (0, 1) for k in (0, 1)]
        corners = numpy.array(corners)
        return numpy.array([corners.min(axis=0), corners.max(axis=0)])

    def __repr__(self):
        where = self.point((0, 0, 0)).round(2).tolist()
        what = self.file or {k: v for k, v in self.params.items()
                             if k in ('size', 'h', 'r1', 'r2', 'center')}
        return f'{self.kind} {what} at {where}'


def export(position=(0.0, 0.0, 0.0), overrides=None):
    """The design's CSG text with the mover at `position`."""
    table = [list(position), list(position)]
    defines = {'data_collection_positions_standard': table}
    defines.update(overrides or {})
    with tempfile.TemporaryDirectory() as directory:
        out = os.path.join(directory, 'layout.csg')
        command = ['openscad', '-o', out]
        for name, value in defines.items():
            command += ['-D', f'{name}={_scad(value)}']
        command.append(LAYOUT)
        subprocess.run(command, check=True, capture_output=True)
        with open(out) as handle:
            return handle.read()


def leaves(position=(0.0, 0.0, 0.0), overrides=None):
    """Every primitive of the design at `position`, with its matrix."""
    return parse(export(position, overrides))


def parse(text):
    found = []
    _walk(text, 0, len(text), numpy.identity(4), None, False, found)
    return found


def _scad(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (list, tuple)):
        return '[' + ', '.join(_scad(v) for v in value) + ']'
    return repr(value)


def _walk(text, start, end, matrix, color, subtracted, found):
    position = start
    while position < end:
        head = _HEAD.match(text, position, end)
        if head is None:
            if text[position].isspace() or text[position] == ';':
                position += 1
                continue
            raise ValueError(f'unreadable CSG at {position}: {text[position:position + 40]!r}')
        name = head.group(1)
        args_start = head.end()
        args_end = _matching(text, args_start - 1, '(', ')')
        args = text[args_start:args_end]
        position = args_end + 1
        while text[position].isspace():
            position += 1
        if text[position] == ';':
            body = None
            position += 1
        elif text[position] == '{':
            body_end = _matching(text, position, '{', '}')
            body = (position + 1, body_end)
            position = body_end + 1
        else:
            raise ValueError(f'expected ; or {{ after {name} at {position}')

        child_matrix, child_color = matrix, color
        if name == 'multmatrix':
            child_matrix = matrix @ numpy.array(ast.literal_eval(args), dtype=float)
        elif name == 'color':
            child_color = tuple(ast.literal_eval(args))

        if name in ('group', 'union', 'multmatrix', 'color', 'intersection', 'hull',
                    'minkowski', 'render'):
            if body:
                _walk(text, body[0], body[1], child_matrix, child_color, subtracted, found)
        elif name == 'difference':
            if body:
                _difference(text, body[0], body[1], child_matrix, child_color, subtracted, found)
        else:
            found.append(Leaf(name, _params(args), matrix, color, subtracted))


def _difference(text, start, end, matrix, color, subtracted, found):
    """The first child is kept, the rest are subtracted."""
    position = start
    first = True
    while position < end:
        head = _HEAD.match(text, position, end)
        if head is None:
            position += 1
            continue
        args_end = _matching(text, head.end() - 1, '(', ')')
        after = args_end + 1
        while text[after].isspace():
            after += 1
        if text[after] == '{':
            stop = _matching(text, after, '{', '}') + 1
        else:
            stop = after + 1
        _walk(text, position, stop, matrix, color, subtracted or not first, found)
        first = False
        position = stop


def _matching(text, open_at, opener, closer):
    depth = 0
    quoted = False
    for index in range(open_at, len(text)):
        char = text[index]
        if quoted:
            if char == '"' and text[index - 1] != '\\':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError('unbalanced CSG')


def _params(args):
    """`key = value, ...` as a dict; a bare leading value is `size`."""
    params = {}
    for item in _split(args):
        if '=' in item:
            key, value = item.split('=', 1)
            params[key.strip()] = _value(value.strip())
        elif item.strip():
            params['size'] = _value(item.strip())
    return params


def _split(args):
    parts, depth, current, quoted = [], 0, '', False
    for char in args:
        if quoted:
            current += char
            if char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char in '[(':
            depth += 1
        elif char in '])':
            depth -= 1
        if char == ',' and depth == 0:
            parts.append(current)
            current = ''
        else:
            current += char
    parts.append(current)
    return parts


def _value(text):
    lowered = text.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    return ast.literal_eval(text)


def echo(expressions):
    """The design's own values for `{name: scad expression}`, evaluated
    with `layout.scad` included."""
    with tempfile.TemporaryDirectory() as directory:
        source = os.path.join(directory, 'echo.scad')
        out = os.path.join(directory, 'echo.echo')
        with open(source, 'w') as handle:
            handle.write(f'include <{LAYOUT}>\n')
            handle.write('echo(' + ', '.join(f'{name}={expr}' for name, expr in expressions.items()) + ');\n')
        subprocess.run(['openscad', '-o', out, source], check=True, capture_output=True)
        with open(out) as handle:
            lines = [line for line in handle if line.startswith('ECHO: ') and '=' in line]
    values = {}
    for line in lines:
        for item in _split(line[len('ECHO: '):].strip()):
            if '=' in item:
                name, value = item.split('=', 1)
                values[name.strip()] = float(value.strip())
    return values
