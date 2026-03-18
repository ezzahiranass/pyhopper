"""Vector2Pt - Create a vector from two points."""

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Vector2Pt(Component):
    """Create an ``AtomicVector`` from point A to point B.

    Optionally unitizes the output vector while also reporting the original
    point-to-point distance.
    """

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("unitize", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("vector", AtomicVector),
        OutputParam("length", float),
    ]

    def generate(self, point_a=None, point_b=None, unitize=False):
        vector = AtomicVector(
            point_b.x - point_a.x,
            point_b.y - point_a.y,
            point_b.z - point_a.z,
        )
        length = vector.length
        if unitize:
            vector = vector.unitize()
        return vector, length
