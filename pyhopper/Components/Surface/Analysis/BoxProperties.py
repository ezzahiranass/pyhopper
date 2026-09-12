"""BoxProperties - Get some properties of a box (Grasshopper "Box Properties")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Boxes import box_corners
from pyhopper.Utils.Vectors import sub


class BoxProperties(Component):
    """Get some properties of a box.

    Inputs:
        box: Box to analyze (Grasshopper Box [item]).

    Outputs:
        center: Center point of box (Grasshopper Center).
        diagonal: Diagonal vector of box (Grasshopper Diagonal).
        area: Area of box (Grasshopper Area).
        volume: Volume of box (Grasshopper Volume).
        degeneracy: Degeneracy of box (Grasshopper Degeneracy).

    Notes:
        Grasshopper: Surface > Analysis > Box Properties (BoxProp).
        pyhopper decisions: ``diagonal`` runs from corner A to corner G (the box's size vector in world
        coordinates), ``area`` and ``volume`` are the usual products and ``degeneracy`` counts the
        zero-length sides — all as Grasshopper reports.
    """

    display_name = "Box Properties"
    nickname = "BoxProp"
    gh_guid = "af9cdb9d-9617-4827-bb3c-9efd88c76a70"

    inputs = [
        InputParam("box", AtomicBox, Access.ITEM),
    ]
    outputs = [
        OutputParam("center", AtomicPoint),
        OutputParam("diagonal", AtomicVector),
        OutputParam("area", float),
        OutputParam("volume", float),
        OutputParam("degeneracy", int),
    ]

    def generate(self, box=None):
        corners = box_corners(box)
        x, y, z = float(box.x_size), float(box.y_size), float(box.z_size)
        return (
            box.plane.origin,
            sub(corners[6], corners[0]),
            2.0 * (x * y + y * z + x * z),
            x * y * z,
            sum(1 for size in (x, y, z) if abs(size) <= 1e-12),
        )
