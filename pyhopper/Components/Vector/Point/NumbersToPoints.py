"""NumbersToPoints - Convert a list of numbers to a list of points (Grasshopper "Numbers to Points")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Points import coordinate_mask


class NumbersToPoints(Component):
    """Convert a list of numbers to a list of points.

    Inputs:
        numbers: Numbers to merge into points (Grasshopper Numbers [list]).
        mask: Mask for coordinate composition (Grasshopper Mask [item]).

    Outputs:
        points: Ordered list of points (Grasshopper Points).

    Notes:
        Grasshopper: Vector > Point > Numbers to Points (Num2Pt).
        pyhopper decisions: the mask (``XYZ`` by default, case-insensitive, any order such as
        ``ZYX``) says which coordinate each number fills, missing coordinates are 0; the number
        count must be a multiple of the mask length and the mask may only use X, Y and Z, otherwise
        ``ValueError`` (Grasshopper warns and emits nothing).
    """

    display_name = "Numbers to Points"
    nickname = "Num2Pt"
    gh_guid = "0ae07da9-951b-4b9b-98ca-d312c252374d"

    inputs = [
        InputParam("numbers", float, Access.LIST, default=[1.0, 2.0, 3.0]),
        InputParam("mask", str, Access.ITEM, default="XYZ"),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
    ]

    def generate(self, numbers=None, mask="XYZ"):
        values = [float(number) for number in (numbers if numbers is not None else [1.0, 2.0, 3.0])]
        slots = coordinate_mask(mask)
        if len(values) % len(slots):
            raise ValueError(f"NumbersToPoints needs a multiple of {len(slots)} numbers for mask {mask!r}")
        points = []
        for start in range(0, len(values), len(slots)):
            coordinates = [0.0, 0.0, 0.0]
            for slot, value in zip(slots, values[start: start + len(slots)]):
                coordinates[slot] = value
            points.append(AtomicPoint(*coordinates))
        return points
