"""PointInTrim - Test whether a {uv} coordinate is inside the trimmed portion of a surface (Grasshopper "Point In Trim")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import uv_in_trim
from pyhopper.Core.TypeSystem import SURFACE


class PointInTrim(Component):
    """Test whether a {uv} coordinate is inside the trimmed portion of a surface.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        uv_point: UV point to test for trim inclusion (Grasshopper UV Point [item]).

    Outputs:
        inclusion: Inclusion flag. TRUE if point is inside the trim boundaries. (Grasshopper Inclusion).

    Notes:
        Grasshopper: Surface > Analysis > Point In Trim (TrimInc).
        pyhopper decisions: Grasshopper-verified — True when the (u, v) coordinate (the point's x and
        y) lies within the surface domain and, for a trimmed surface, inside the outer loop and outside
        the holes; edges count as inside.
    """

    display_name = "Point In Trim"
    nickname = "TrimInc"
    gh_guid = "f881810b-96de-4668-a95a-f9a6d683e65c"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("uv_point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
    ]
    outputs = [
        OutputParam("inclusion", bool),
    ]

    def generate(self, surface=None, uv_point=AtomicPoint.origin()):
        return uv_in_trim(surface, float(uv_point.x), float(uv_point.y))
