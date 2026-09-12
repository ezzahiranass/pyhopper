"""Discontinuity - Find all discontinuities along a curve (Grasshopper "Discontinuity")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import discontinuities
from pyhopper.Core.TypeSystem import CURVE


class Discontinuity(Component):
    """Find all discontinuities along a curve.

    Inputs:
        curve: Curve to analyze (Grasshopper Curve [item]).
        level: Level of discontinuity to test for (1=C1, 2=C2, 3=Cinfinite) (Grasshopper Level [item]).

    Outputs:
        points: Points at discontinuities (Grasshopper Points).
        parameters: Curve parameters at discontinuities (Grasshopper Parameters).

    Notes:
        Grasshopper: Curve > Analysis > Discontinuity (Disc).
        pyhopper decisions: Grasshopper-verified — the ends of an open curve (the seam of a closed
        polyline once) plus every interior parameter where the tangent direction jumps (level 1), the
        tangent or the curvature vector jumps (level 2) or any interior knot/vertex (level 3, C∞);
        collinear polyline vertices are smooth, circles, arcs and ellipses have no interior
        discontinuities. Other levels raise ``ValueError``. Parameters are the curve's native ones.
        Default level 1.
    """

    display_name = "Discontinuity"
    nickname = "Disc"
    gh_guid = "269eaa85-9997-4d77-a9ba-4c58cb45c9d3"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("level", int, Access.ITEM, default=1),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("parameters", float, access=Access.LIST),
    ]

    def generate(self, curve=None, level=1):
        return discontinuities(curve, int(level))
