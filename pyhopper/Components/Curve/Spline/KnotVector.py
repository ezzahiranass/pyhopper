"""KnotVector - Construct a nurbs curve knot vector (Grasshopper "Knot Vector")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveEditing import rhino_knot_vector


class KnotVector(Component):
    """Construct a nurbs curve knot vector.

    Inputs:
        count: Control point count. (Grasshopper Count [item]).
        degree: Curve Degree. (Grasshopper Degree [item]).
        periodic: Curve periodicity (Grasshopper Periodic [item]).

    Outputs:
        knots: Nurbs Knot Vector. (Grasshopper Knots).

    Notes:
        Grasshopper: Curve > Spline > Knot Vector (Knots).
        pyhopper decisions: Grasshopper-verified — Rhino-style knots (without the superfluous end
        knots): clamped integer knots ``0 … 0, 1, 2 …, n-d … n-d`` or the uniform run ``0 … n+d-2``
        for periodic curves; a degree above ``count - 1`` is clamped to it as in Grasshopper. The
        count is required; degree defaults to 3.
    """

    display_name = "Knot Vector"
    nickname = "Knots"
    gh_guid = "846470bd-4918-4d00-9388-7e022b2cba73"

    inputs = [
        InputParam("count", int, Access.ITEM),
        InputParam("degree", int, Access.ITEM, default=3),
        InputParam("periodic", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("knots", float, access=Access.LIST),
    ]

    def generate(self, count, degree=3, periodic=False):
        return rhino_knot_vector(int(count), int(degree), bool(periodic))
