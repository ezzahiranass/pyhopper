"""Degrees - Convert an angle specified in radians to degrees (Grasshopper "Degrees")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Degrees(Component):
    """Convert an angle specified in radians to degrees.

    Inputs:
        radians: Angle in radians (Grasshopper Radians [item]).

    Outputs:
        degrees: Angle in degrees (Grasshopper Degrees).

    Notes:
        Grasshopper: Maths > Trig > Degrees (Deg).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Degrees"
    nickname = "Deg"
    gh_guid = "0d77c51e-584f-44e8-aed2-c2ddf4803888"

    inputs = [
        InputParam("radians", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("degrees", float),
    ]

    def generate(self, radians=0.0):
        return math.degrees(float(radians))
