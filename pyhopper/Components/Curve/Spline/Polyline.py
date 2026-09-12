"""Polyline - Connect vertices with straight line segments."""

from pyhopper.Core.Atoms import AtomicPoint, AtomicPolyline
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam



class Polyline(Component):
    """Create one ``AtomicPolyline`` from each branch of vertices."""

    display_name = "PolyLine"
    nickname = "PLine"
    gh_guid = "71b5b089-500a-4ea6-81c5-2f960441a0e8"

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
        if closed and points[0] != points[-1]:
            points += (points[0],)
        return AtomicPolyline(points=points)
