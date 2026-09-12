"""CurveLine - Solve intersection events for a curve and a line (Grasshopper "Curve | Line")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import curve_line_intersections


class CurveLine(Component):
    """Solve intersection events for a curve and a line.

    Inputs:
        curve: Curve to intersect (Grasshopper Curve [item]).
        line: Line to intersect with (Grasshopper Line [item]).

    Outputs:
        points: Intersection events (Grasshopper Points).
        params: Parameters on curve (Grasshopper Params).
        count: Number of intersection events (Grasshopper Count).

    Notes:
        Grasshopper: Intersect > Mathematical > Curve | Line (CLX).
        pyhopper decisions: Grasshopper-verified — the line is infinite (the segment only fixes its
        direction); events are sorted by curve parameter (native domain), points lie on the curve and
        ``count`` is the number of events. Coincidence uses pyhopper's absolute tolerance (0.01, Rhino's
        default document tolerance that Grasshopper uses).
    """

    display_name = "Curve | Line"
    nickname = "CLX"
    gh_guid = "0e3173b6-91c6-4845-a748-e45d4fdbc262"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("line", AtomicLine, Access.ITEM),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("params", float, access=Access.LIST),
        OutputParam("count", int),
    ]

    def generate(self, curve=None, line=None):
        events = curve_line_intersections(curve, line)
        return [point for _, point in events], [t for t, _ in events], len(events)
