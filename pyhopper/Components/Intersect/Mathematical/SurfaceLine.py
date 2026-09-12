"""SurfaceLine - Solve intersection events for a surface and a line (Grasshopper "Surface | Line")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE, SURFACE
from pyhopper.Utils.Intersections import surface_line_intersections, surface_line_overlaps


class SurfaceLine(Component):
    """Solve intersection events for a surface and a line.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        line: Intersection line (Grasshopper Line [item]).

    Outputs:
        curves: Intersection overlap curves (Grasshopper Curves).
        points: Intersection points (Grasshopper Points).
        uv_points: Surface {uv} coordinates at intersection events (Grasshopper UV Points).
        normal: Surface normal vector at intersection events (Grasshopper Normal).

    Notes:
        Grasshopper: Intersect > Mathematical > Surface | Line (SLX).
        pyhopper decisions: Grasshopper-verified — the line is infinite; piercing points come with
        the surface ``(u, v, 0)`` parameters and unit normals, ordered along the line. A line lying in a
        planar surface is an overlap: the stretches inside the surface come out as lines in ``curves``
        and the point outputs stay empty, as in Grasshopper (which returns them as degree-1 curves).
    """

    display_name = "Surface | Line"
    nickname = "SLX"
    gh_guid = "a834e823-ae01-44d8-9066-c138eeb6f391"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("line", AtomicLine, Access.ITEM),
    ]
    outputs = [
        OutputParam("curves", CURVE, access=Access.LIST),
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("uv_points", AtomicPoint, access=Access.LIST),
        OutputParam("normal", AtomicVector, access=Access.LIST),
    ]

    def generate(self, surface=None, line=None):
        overlaps = surface_line_overlaps(surface, line)
        if overlaps:
            return overlaps, [], [], []
        hits = surface_line_intersections(surface, line)
        return [], [point for _, _, point, _, _ in hits], [AtomicPoint(u, v, 0.0) for u, v, _, _, _ in hits], [normal for _, _, _, normal, _ in hits]
