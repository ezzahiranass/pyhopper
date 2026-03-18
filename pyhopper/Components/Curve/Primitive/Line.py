"""Line - Create a line from two points."""

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Line(Component):
    """Create an ``AtomicLine`` atom between two points."""

    inputs = [
        InputParam("start", AtomicPoint, Access.ITEM),
        InputParam("end", AtomicPoint, Access.ITEM),
    ]
    outputs = [OutputParam("line")]

    def generate(self, start=None, end=None):
        return AtomicLine(start=start, end=end)
