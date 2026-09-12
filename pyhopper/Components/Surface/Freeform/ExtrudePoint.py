"""ExtrudePoint - Extrude curves and surfaces to a point (Grasshopper "Extrude Point")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import SURFACE
from pyhopper.Utils.SurfaceBuilders import extrude_to_point
from pyhopper.Core.TypeSystem import GEOMETRY


class ExtrudePoint(Component):
    """Extrude curves and surfaces to a point.

    Inputs:
        base: Profile curve or surface (Grasshopper Base [item]).
        point: Extrusion tip (Grasshopper Point [item]).

    Outputs:
        extrusion: Extrusion result (Grasshopper Extrusion).

    Notes:
        Grasshopper: Surface > Freeform > Extrude Point (Extr).
        pyhopper decisions: curves only: a ruled surface from the curve (V, its own knots) to the apex (U, domain =
        distance from the curve start to the apex), exactly Grasshopper's construction; a polyline
        becomes one kinked surface where Grasshopper splits faces; surfaces as base (Grasshopper
        builds a capped pyramid brep) raise ``TypeError`` until capping exists.
    """

    display_name = "Extrude Point"
    nickname = "Extr"
    gh_guid = "be6636b2-2f1a-4d42-897b-fdef429b6f17"

    inputs = [
        InputParam("base", GEOMETRY, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("extrusion", SURFACE),
    ]

    def generate(self, base=None, point=None):
        from pyhopper.Core.TypeSystem import CURVE_TYPES
        from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
        if not isinstance(base, CURVE_TYPES):
            raise TypeError("Extrude Point supports curves; surface bases need capping (not yet available)")
        return extrude_to_point(as_nurbs_curve(base), point)
