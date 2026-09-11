"""ConstructPoint - Construct a point from XYZ coordinates."""

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ConstructPoint(Component):
    """Construct an ``AtomicPoint`` from X, Y, and Z coordinates."""

    inputs = [
        InputParam("x_coordinate", float, Access.ITEM, default=0.0),
        InputParam("y_coordinate", float, Access.ITEM, default=0.0),
        InputParam("z_coordinate", float, Access.ITEM, default=0.0),
    ]
    outputs = [OutputParam("point", AtomicPoint)]

    def generate(self, x_coordinate=0.0, y_coordinate=0.0, z_coordinate=0.0):
        return AtomicPoint(
            float(x_coordinate),
            float(y_coordinate),
            float(z_coordinate),
        )
