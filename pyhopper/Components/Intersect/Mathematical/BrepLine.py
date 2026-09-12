"""BrepLine - Solve intersection events for a Brep and a line (Grasshopper "Brep | Line")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBrep, AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import brep_line_intersections


class BrepLine(Component):
    """Solve intersection events for a Brep and a line.

    Inputs:
        brep: Base Brep (Grasshopper Brep [item]).
        line: Intersection line (Grasshopper Line [item]).

    Outputs:
        curves: Intersection overlap curves (Grasshopper Curves).
        points: Intersection points (Grasshopper Points).

    Notes:
        Grasshopper: Intersect > Mathematical > Brep | Line (BLX).
        pyhopper decisions: Grasshopper-verified — the line is infinite; the piercing points are
        listed face by face in Rhino's face order (for a box: bottom, -y, +x, +y, -x, top), each point
        once. Stretches of the line lying in a planar face are overlaps: they come out as lines in
        ``curves`` and their end points are not repeated in ``points``, as in Grasshopper (which returns
        overlaps as degree-1 curves). Boxes and surfaces are accepted as breps.
    """

    display_name = "Brep | Line"
    nickname = "BLX"
    gh_guid = "ed0742f9-6647-4d95-9dfd-9ad17080ae9c"

    inputs = [
        InputParam("brep", AtomicBrep, Access.ITEM),
        InputParam("line", AtomicLine, Access.ITEM),
    ]
    outputs = [
        OutputParam("curves", CURVE, access=Access.LIST),
        OutputParam("points", AtomicPoint, access=Access.LIST),
    ]

    def generate(self, brep=None, line=None):
        overlaps, points = brep_line_intersections(brep, line)
        return overlaps, points
