"""MultipleCurves - Solve intersection events for multiple curves (Grasshopper "Multiple Curves")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import curve_curve_intersections


class MultipleCurves(Component):
    """Solve intersection events for multiple curves.

    Inputs:
        curves: Curves to intersect (Grasshopper Curves [list]).

    Outputs:
        points: Intersection events (Grasshopper Points).
        index_a: Index of first intersection curve (Grasshopper Index A).
        index_b: Index of second intersection curve (Grasshopper Index B).
        param_a: Parameter on first curve (Grasshopper Param A).
        param_b: Parameter on second curve (Grasshopper Param B).

    Notes:
        Grasshopper: Intersect > Physical > Multiple Curves (MCX).
        pyhopper decisions: Grasshopper-verified — every pair ``i < j`` in index order, its events sorted
        along curve ``i`` (points at the midpoint of the two curve points, native parameters); self-
        intersections are not included. Coincidence uses pyhopper's absolute tolerance (0.01, Rhino's
        default document tolerance that Grasshopper uses).
    """

    display_name = "Multiple Curves"
    nickname = "MCX"
    gh_guid = "931e6030-ccb3-4a7b-a89a-99dcce8770cd"

    inputs = [
        InputParam("curves", CURVE, Access.LIST),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("index_a", int, access=Access.LIST),
        OutputParam("index_b", int, access=Access.LIST),
        OutputParam("param_a", float, access=Access.LIST),
        OutputParam("param_b", float, access=Access.LIST),
    ]

    def generate(self, curves=None):
        curves = list(curves or [])
        points, index_a, index_b, param_a, param_b = [], [], [], [], []
        for i, first in enumerate(curves):
            for j in range(i + 1, len(curves)):
                for ta, tb, point in curve_curve_intersections(first, curves[j]):
                    points.append(point)
                    index_a.append(i)
                    index_b.append(j)
                    param_a.append(ta)
                    param_b.append(tb)
        return points, index_a, index_b, param_a, param_b
