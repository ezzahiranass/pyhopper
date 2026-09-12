"""Polyline - Connect vertices with straight line segments."""

from pyhopper.Core.Atoms import AtomicPoint, AtomicPolyline
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _first(value, default):
    if isinstance(value, list):
        return value[0] if value else default
    return value


class Polyline(Component):
    """Create one ``AtomicPolyline`` from each branch of vertices."""

    inputs = [
        InputParam("vertices", AtomicPoint, Access.LIST),
        InputParam("closed", bool, Access.ITEM, default=False),
    ]
    outputs = [OutputParam("polyline", AtomicPolyline)]

    def generate(self, vertices=None, closed=False):
        points = tuple(vertices or ())
        if len(points) < 2:
            raise ValueError("Polyline requires at least two vertices")
        if not all(isinstance(point, AtomicPoint) for point in points):
            raise TypeError("Polyline vertices must all be AtomicPoint values")
        if bool(_first(closed, False)) and points[0] != points[-1]:
            points += (points[0],)
        return AtomicPolyline(points=points)
