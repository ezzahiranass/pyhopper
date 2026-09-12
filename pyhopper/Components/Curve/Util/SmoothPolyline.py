"""SmoothPolyline - Smooth the vertices of a polyline curve (Grasshopper "Smooth Polyline")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicPolyline
from pyhopper.Utils.CurveEditing import polyline_points, smooth_polyline
from pyhopper.Core.TypeSystem import CURVE


class SmoothPolyline(Component):
    """Smooth the vertices of a polyline curve.

    Inputs:
        polyline: Polyline to smooth (Grasshopper Polyline [item]).
        strength: Smoothing strength (0 = none, 1 = maximum) (Grasshopper Strength [item]).
        times: Number of times to apply the smoothing operation (Grasshopper Times [item]).

    Outputs:
        polyline: Smoothed polyline (Grasshopper Polyline).

    Notes:
        Grasshopper: Curve > Util > Smooth Polyline (SmoothPLine).
        pyhopper decisions: Grasshopper-verified — every pass moves each vertex ``strength / 2`` of the
        way towards the midpoint of its neighbours (all vertices at once); the ends of an open
        polyline stay put, a closed polyline wraps around. Defaults: strength 1, one pass.
    """

    display_name = "Smooth Polyline"
    nickname = "SmoothPLine"
    gh_guid = "5c5fbc42-3e1d-4081-9cf1-148d0b1d9610"

    inputs = [
        InputParam("polyline", CURVE, Access.ITEM),
        InputParam("strength", float, Access.ITEM, default=1.0),
        InputParam("times", int, Access.ITEM, default=1),
    ]
    outputs = [
        OutputParam("polyline", CURVE),
    ]

    def generate(self, polyline=None, strength=1.0, times=1):
        return AtomicPolyline(tuple(smooth_polyline(polyline_points(polyline), float(strength), int(times))))
