"""OsculatingCircles - Calculate the principal osculating circles of a surface at a {uv} coordinate (Grasshopper "Osculating Circles")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import osculating_circle, surface_analysis
from pyhopper.Core.TypeSystem import CURVE, SURFACE


class OsculatingCircles(Component):
    """Calculate the principal osculating circles of a surface at a {uv} coordinate.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        point: {uv} coordinate to evaluate (Grasshopper Point [item]).

    Outputs:
        point: Surface point at {uv} coordinate (Grasshopper Point).
        first_circle: First osculating circle (Grasshopper First circle).
        second_circle: Second osculating circle (Grasshopper Second circle).

    Notes:
        Grasshopper: Surface > Analysis > Osculating Circles (Osc).
        pyhopper decisions: Grasshopper-verified — the circles of the two principal curvatures (first
        the larger absolute curvature): centre ``point + normal / κ``, x axis along the principal
        direction, plane normal ``direction × normal``; a flat direction gives Grasshopper's 10-long
        line through the point instead. ``point`` carries the (u, v) coordinate in its x and y.
    """

    display_name = "Osculating Circles"
    nickname = "Osc"
    gh_guid = "b799b7c0-76df-4bdb-b3cc-401b1d021aa5"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("first_circle", CURVE),
        OutputParam("second_circle", CURVE),
    ]

    def generate(self, surface=None, point=AtomicPoint.origin()):
        analysis = surface_analysis(surface, point.x, point.y)
        return analysis.point, osculating_circle(analysis, analysis.maximum, analysis.max_direction), osculating_circle(analysis, analysis.minimum, analysis.min_direction)
