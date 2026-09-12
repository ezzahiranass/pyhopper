"""Seam - Adjust the seam of a closed curve (Grasshopper "Seam")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import change_seam
from pyhopper.Core.TypeSystem import CURVE


class Seam(Component):
    """Adjust the seam of a closed curve.

    Inputs:
        curve: Curve to adjust (Grasshopper Curve [item]).
        seam: Parameter of new seam (Grasshopper Seam [item]).

    Outputs:
        curve: Adjusted curve (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Seam (Seam).
        pyhopper decisions: Grasshopper-verified — circles rotate their plane to the new start,
        closed polylines rotate their vertices (inserting one for a mid-edge seam), closed NURBS
        curves are split and rejoined with a C0 knot at the old seam on the original domain
        (Grasshopper re-seams periodic curves with its own knot vector), polycurves rotate their
        segments; open curves come back unchanged (Grasshopper warns). Grasshopper has no default
        seam; pyhopper's 0 leaves the curve alone.
    """

    display_name = "Seam"
    nickname = "Seam"
    gh_guid = "42ad8dc1-b0c0-40df-91f5-2c46e589e6c2"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("seam", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, curve=None, seam=0.0):
        return change_seam(curve, float(seam))
