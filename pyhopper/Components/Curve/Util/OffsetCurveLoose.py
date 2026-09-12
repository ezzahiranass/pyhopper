"""OffsetCurveLoose - Offset the control-points of a curve with a specified distance (Grasshopper "Offset Curve Loose")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveEditing import offset_control_polygon
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Core.TypeSystem import CURVE


class OffsetCurveLoose(Component):
    """Offset the control-points of a curve with a specified distance.

    Inputs:
        curve: Curve to offset (Grasshopper Curve [item]).
        distance: Offset distance (Grasshopper Distance [item]).
        plane: Optional Plane for offset operation (Grasshopper Plane [item]).

    Outputs:
        curve: Resulting offset (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Offset Curve Loose (Offset (L)).
        pyhopper decisions: Grasshopper-verified — the control polygon is offset: end control points
        move ``distance`` along ``edge × normal``, interior ones along their bisector crossed with the
        normal by ``distance / cos(half the turn)``, so positive distances go to the right of the
        curve seen against the plane normal; without a plane Grasshopper uses World XY even for tilted
        planar curves (its fallback for non-planar curves is undocumented and not replicated). Named
        curves are converted to NURBS first (pyhopper's conversions live on the [0, 1] domain).
        Default distance 1.
    """

    display_name = "Offset Curve Loose"
    nickname = "Offset (L)"
    gh_guid = "80e55fc2-933b-4bfb-a353-12358786dba8"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("distance", float, Access.ITEM, default=1.0),
        InputParam("plane", AtomicPlane, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, curve=None, distance=1.0, plane=None):
        return offset_control_polygon(as_nurbs_curve(curve), float(distance), plane if plane is not None else AtomicPlane.world_xy())
