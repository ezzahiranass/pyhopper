"""CurveNearestObject - Find the object nearest to a curve (Grasshopper "Curve Nearest Object")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import curve_geometry_closest
from pyhopper.Core.TypeSystem import CURVE, GEOMETRY


class CurveNearestObject(Component):
    """Find the object nearest to a curve.

    Inputs:
        curve: Curve to search from (Grasshopper Curve [item]).
        geometry: Shapes to search (Grasshopper Geometry [list]).

    Outputs:
        point_a: Point on curve closest to nearest shape (Grasshopper Point A).
        point_b: Point on nearest shape closest to curve (Grasshopper Point B).
        index: Index of nearest shape (Grasshopper Index).

    Notes:
        Grasshopper: Curve > Analysis > Curve Nearest Object (CrvNear).
        pyhopper decisions: Grasshopper-verified — the geometry item (point, curve, plane, surface,
        brep or box) nearest to the curve, with the closest point on the curve (A), on the item (B) and
        its index; equal distances go to the last item, as Grasshopper does. An empty list emits nothing.
    """

    display_name = "Curve Nearest Object"
    nickname = "CrvNear"
    gh_guid = "748f214a-bc64-4556-9da5-4fa59a30c5c7"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("geometry", GEOMETRY, Access.LIST),
    ]
    outputs = [
        OutputParam("point_a", AtomicPoint),
        OutputParam("point_b", AtomicPoint),
        OutputParam("index", int),
    ]

    def generate(self, curve=None, geometry=None):
        best = None
        for index, item in enumerate(geometry or []):
            point_a, point_b, d = curve_geometry_closest(curve, item)
            if best is None or d <= best[2] + 1e-12:
                best = (point_a, point_b, d, index)
        if best is None:
            return Component.NO_OUTPUT, Component.NO_OUTPUT, Component.NO_OUTPUT
        return best[0], best[1], best[3]
