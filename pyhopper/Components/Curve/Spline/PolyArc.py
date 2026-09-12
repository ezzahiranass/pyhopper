"""PolyArc - Create a polycurve consisting of arc and line segments (Grasshopper "PolyArc")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import polyarc
from pyhopper.Core.TypeSystem import CURVE


class PolyArc(Component):
    """Create a polycurve consisting of arc and line segments.

    Inputs:
        vertices: Polyarc vertex coordinates (Grasshopper Vertices [list]).
        tangent: Optional tangent vector at start. (Grasshopper Tangent [item]).
        closed: Close the polyarc curve. (Grasshopper Closed [item]).

    Outputs:
        poly_arc: Resulting polyarc curve (Grasshopper PolyArc).

    Notes:
        Grasshopper: Curve > Spline > PolyArc (PArc).
        pyhopper decisions: Grasshopper-verified — arcs through consecutive vertices, each tangent to
        the previous segment (the first to the given tangent); a segment whose tangent runs along its
        chord is a line. Without a tangent the first segment is a line along the first chord
        (Grasshopper emits degenerate arcs there). ``closed`` adds an equal-tangent biarc back to the
        start (Grasshopper closes with its own arc blend). Two vertices give the bare segment.
    """

    display_name = "PolyArc"
    nickname = "PArc"
    gh_guid = "7159ef59-e4ef-44b8-8cb2-91231e278292"

    inputs = [
        InputParam("vertices", AtomicPoint, Access.LIST),
        InputParam("tangent", AtomicVector, Access.ITEM, optional=True),
        InputParam("closed", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("poly_arc", CURVE),
    ]

    def generate(self, vertices=None, tangent=None, closed=False):
        return polyarc(list(vertices or []), tangent, bool(closed))
