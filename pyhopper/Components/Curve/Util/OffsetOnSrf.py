"""OffsetOnSrf - Offset a curve on a surface with a specified distance (Grasshopper "Offset on Srf")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurvesOnSurfaces import offset_on_surface
from pyhopper.Core.TypeSystem import CURVE, SURFACE


class OffsetOnSrf(Component):
    """Offset a curve on a surface with a specified distance.

    Inputs:
        curve: Curve to offset (Grasshopper Curve [item]).
        distance: Offset distance (Grasshopper Distance [item]).
        surface: Surface for offset operation (Grasshopper Surface [item]).

    Outputs:
        curve: Resulting offsets (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Offset on Srf (OffsetS).
        pyhopper decisions: Grasshopper-verified for straight curves on planar surfaces (the offset
        polyline with mitred corners, to the left of the curve seen along the surface normal; a line
        gives a two-point polyline like Rhino); other cases move samples along the in-surface
        perpendicular, pull them back onto the surface and interpolate, which Rhino refits differently
        (structural comparison only). Default distance 1.
    """

    display_name = "Offset on Srf"
    nickname = "OffsetS"
    gh_guid = "b6f5cb51-f260-4c74-bf73-deb47de1bf91"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("distance", float, Access.ITEM, default=1.0),
        InputParam("surface", SURFACE, Access.ITEM),
    ]
    outputs = [
        OutputParam("curve", CURVE, access=Access.LIST),
    ]

    def generate(self, curve=None, distance=1.0, surface=None):
        return offset_on_surface(curve, float(distance), surface)
