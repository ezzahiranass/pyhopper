"""Round - Round a floating point value (Grasshopper "Round")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _round_half_away_from_zero(value: float) -> int:
    magnitude = math.floor(abs(value) + 0.5)
    return magnitude if value >= 0.0 else -magnitude


class Round(Component):
    """Round a floating point value.

    Inputs:
        number: Number to round (Grasshopper Number [item]).

    Outputs:
        nearest: Integer nearest to x (Grasshopper Nearest).
        floor: First integer smaller than or equal to x (Grasshopper Floor).
        ceiling: First integer larger than or equal to x (Grasshopper Ceiling).

    Notes:
        Grasshopper: Maths > Util > Round (Round).
        pyhopper decisions: ``nearest`` rounds halves away from zero (2.5 -> 3, -2.5 -> -3), the rule the
        type system uses for ``int`` inputs.
    """

    display_name = "Round"
    nickname = "Round"
    gh_guid = "a50c4a3b-0177-4c91-8556-db95de6c56c8"

    inputs = [
        InputParam("number", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("nearest", int),
        OutputParam("floor", int),
        OutputParam("ceiling", int),
    ]

    def generate(self, number=0.0):
        x = float(number)
        return _round_half_away_from_zero(x), math.floor(x), math.ceil(x)
