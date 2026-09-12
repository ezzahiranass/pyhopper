"""PointsToNumbers - Convert a list of points to a list of numbers (Grasshopper "Points to Numbers")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Points import coordinate_mask


class PointsToNumbers(Component):
    """Convert a list of points to a list of numbers.

    Inputs:
        points: Points to parse (Grasshopper Points [list]).
        mask: Mask for coordinate extraction (Grasshopper Mask [item]).

    Outputs:
        numbers: Ordered list of coordinates (Grasshopper Numbers).

    Notes:
        Grasshopper: Vector > Point > Points to Numbers (Pt2Num).
        pyhopper decisions: every point contributes the coordinates the mask names, in the mask's
        order (``XYZ`` by default, case-insensitive); an invalid mask raises ``ValueError``.
    """

    display_name = "Points to Numbers"
    nickname = "Pt2Num"
    gh_guid = "d24169cc-9922-4923-92bc-b9222efc413f"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST, default=[AtomicPoint(1.0, 2.0, 3.0)]),
        InputParam("mask", str, Access.ITEM, default="XYZ"),
    ]
    outputs = [
        OutputParam("numbers", float, access=Access.LIST),
    ]

    def generate(self, points=None, mask="XYZ"):
        slots = coordinate_mask(mask)
        numbers = []
        for point in (points if points is not None else [AtomicPoint(1.0, 2.0, 3.0)]):
            coordinates = (float(point.x), float(point.y), float(point.z))
            numbers.extend(coordinates[slot] for slot in slots)
        return numbers
