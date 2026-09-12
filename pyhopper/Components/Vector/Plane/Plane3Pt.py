"""Plane3Pt - Create a plane through three points (Grasshopper "Plane 3Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import plane_from_points


class Plane3Pt(Component):
    """Create a plane through three points.

    Inputs:
        point_a: Origin point (Grasshopper Point A [item]).
        point_b: X-direction point (Grasshopper Point B [item]).
        point_c: Orientation point (Grasshopper Point C [item]).

    Outputs:
        plane: Plane definition (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Plane 3Pt (Pl 3Pt).
        pyhopper decisions: origin at A, x axis towards B, normal ``(B - A) x (C - A)`` (flips when C is on the
        other side), like Grasshopper; collinear points raise ``ValueError``.
    """

    display_name = "Plane 3Pt"
    nickname = "Pl 3Pt"
    gh_guid = "c98a6015-7a2f-423c-bc66-bdc505249b45"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("point_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, point_a=None, point_b=None, point_c=None):
        return plane_from_points(point_a, point_b, point_c)
