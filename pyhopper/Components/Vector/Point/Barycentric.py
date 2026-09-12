"""Barycentric - Create a point from barycentric {u,v,w} coordinates (Grasshopper "Barycentric")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Barycentric(Component):
    """Create a point from barycentric {u,v,w} coordinates.

    Inputs:
        point_a: First anchor point (Grasshopper Point A [item]).
        point_b: Second anchor point (Grasshopper Point B [item]).
        point_c: Third anchor point (Grasshopper Point C [item]).
        coordinate_u: First barycentric coordinate (Grasshopper Coordinate U [item]).
        coordinate_v: Second barycentric coordinate (Grasshopper Coordinate V [item]).
        coordinate_w: Third barycentric coordinate (Grasshopper Coordinate W [item]).

    Outputs:
        point: Barycentric point coordinate (Grasshopper Point).

    Notes:
        Grasshopper: Vector > Point > Barycentric (BCentric).
        pyhopper decisions: ``(U A + V B + W C) / (U + V + W)`` — the coordinates need not be
        normalised (defaults 1, 1, 1 give the centroid); a zero sum raises ``ValueError`` where
        Grasshopper emits null.
    """

    display_name = "Barycentric"
    nickname = "BCentric"
    gh_guid = "9adffd61-f5d1-4e9e-9572-e8d9145730dc"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("point_b", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("point_c", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("coordinate_u", float, Access.ITEM, default=1.0),
        InputParam("coordinate_v", float, Access.ITEM, default=1.0),
        InputParam("coordinate_w", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
    ]

    def generate(self, point_a=AtomicPoint.origin(), point_b=AtomicPoint.origin(), point_c=AtomicPoint.origin(), coordinate_u=1.0, coordinate_v=1.0, coordinate_w=1.0):
        u, v, w = float(coordinate_u), float(coordinate_v), float(coordinate_w)
        total = u + v + w
        if total == 0.0:
            raise ValueError("Barycentric coordinates must not sum to zero")
        return AtomicPoint(
            (u * point_a.x + v * point_b.x + w * point_c.x) / total,
            (u * point_a.y + v * point_b.y + w * point_c.y) / total,
            (u * point_a.z + v * point_b.z + w * point_c.z) / total,
        )
