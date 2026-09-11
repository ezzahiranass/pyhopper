"""DeconstructPoint - Split a point into its XYZ components."""

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DeconstructPoint(Component):
    """Return the X, Y, and Z components of an ``AtomicPoint``."""

    inputs = [InputParam("point", AtomicPoint, Access.ITEM)]
    outputs = [
        OutputParam("x_component", float),
        OutputParam("y_component", float),
        OutputParam("z_component", float),
    ]

    def generate(self, point=None):
        return float(point.x), float(point.y), float(point.z)
