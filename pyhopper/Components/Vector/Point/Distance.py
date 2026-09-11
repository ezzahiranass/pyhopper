"""Distance - Measure the Euclidean distance between two points."""

import math

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Distance(Component):
    """Compute the Euclidean distance between two point coordinates."""

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
    ]
    outputs = [OutputParam("distance", float)]

    def generate(self, point_a=None, point_b=None):
        return math.sqrt(
            (point_b.x - point_a.x) ** 2
            + (point_b.y - point_a.y) ** 2
            + (point_b.z - point_a.z) ** 2
        )
