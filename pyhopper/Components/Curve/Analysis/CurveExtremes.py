"""CurveExtremes - Find the extremes (highest and lowest points) on a curve (Grasshopper "Extremes")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import curve_extremes
from pyhopper.Core.TypeSystem import CURVE


class CurveExtremes(Component):
    """Find the extremes (highest and lowest points) on a curve.

    Inputs:
        curve: Base curve (Grasshopper Curve [item]).
        plane: Plane for extreme direction. (Grasshopper Plane [item]).

    Outputs:
        highest: Highest point on curve. (Grasshopper Highest).
        lowest: Lowest point on curve. (Grasshopper Lowest).

    Notes:
        Grasshopper: Curve > Analysis > Extremes (X-tremez).
        pyhopper decisions: Grasshopper-verified — the curve points highest and lowest along the
        plane's normal (default World XY), from the ends, polyline vertices and the interior parameters
        where the height is stationary; ties go to the earliest parameter (Grasshopper's choice on flat
        stretches is arbitrary).
    """

    display_name = "Extremes"
    nickname = "X-tremez"
    gh_guid = "ebd6c758-19ae-4d74-aed7-b8a0392ff743"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("highest", AtomicPoint),
        OutputParam("lowest", AtomicPoint),
    ]

    def generate(self, curve=None, plane=AtomicPlane.world_xy()):
        return curve_extremes(curve, plane)
