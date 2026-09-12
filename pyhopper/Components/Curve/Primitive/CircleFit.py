"""CircleFit - Fit a circle to a collection of points (Grasshopper "Circle Fit")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicCircle, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveFitting import fit_circle


class CircleFit(Component):
    """Fit a circle to a collection of points.

    Inputs:
        points: Points to fit (Grasshopper Points [list]).

    Outputs:
        circle: Resulting circle (Grasshopper Circle).
        radius: Circle radius (Grasshopper Radius).
        deviation: Maximum distance between circle and points (Grasshopper Deviation).

    Notes:
        Grasshopper: Curve > Primitive > Circle Fit (FCircle).
        pyhopper decisions: geometric least-squares circle in the least-squares plane of the points
        (matches Grasshopper's centre, radius and deviation); ``deviation`` is the largest radial
        error; fewer than three or collinear points raise ``ValueError`` (Grasshopper emits nulls).
    """

    display_name = "Circle Fit"
    nickname = "FCircle"
    gh_guid = "be52336f-a2e1-43b1-b5f5-178ba489508a"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
    ]
    outputs = [
        OutputParam("circle", AtomicCircle),
        OutputParam("radius", float),
        OutputParam("deviation", float),
    ]

    def generate(self, points=None):
        circle, deviation = fit_circle(list(points or []))
        return circle, circle.radius, deviation
