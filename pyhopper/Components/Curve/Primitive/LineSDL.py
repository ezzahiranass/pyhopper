"""LineSDL - Create a line from start point, direction, and length."""

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class LineSDL(Component):
    """Create an ``AtomicLine`` from start point, direction, and length.

    The direction vector is unitized before the line is constructed.
    """

    inputs = [
        InputParam("start", AtomicPoint, Access.ITEM),
        InputParam("direction", AtomicVector, Access.ITEM),
        InputParam("length", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("line")]

    def generate(self, start=None, direction=None, length=1.0):
        direction_unit = direction.unitize()
        distance = float(length)
        end = AtomicPoint(
            start.x + direction_unit.x * distance,
            start.y + direction_unit.y * distance,
            start.z + direction_unit.z * distance,
        )
        return AtomicLine(start=start, end=end)
