"""Radians - Convert an angle specified in degrees to radians (Grasshopper "Radians")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Radians(Component):
    """Convert an angle specified in degrees to radians.

    Inputs:
        degrees: Angle in degrees (Grasshopper Degrees [item]).

    Outputs:
        radians: Angle in radians (Grasshopper Radians).

    Notes:
        Grasshopper: Maths > Trig > Radians (Rad).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Radians"
    nickname = "Rad"
    gh_guid = "a4cd2751-414d-42ec-8916-476ebf62d7fe"

    inputs = [
        InputParam("degrees", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("radians", float),
    ]

    def generate(self, degrees=0.0):
        return math.radians(float(degrees))
