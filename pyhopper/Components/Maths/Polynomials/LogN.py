"""LogN - Return the N-base logarithm of a number (Grasshopper "Log N")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class LogN(Component):
    """Return the N-base logarithm of a number.

    Inputs:
        number: Value (Grasshopper Number [item]).
        base: Logarithm base (Grasshopper Base [item]).

    Outputs:
        result: Result (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Log N (LogN).
        pyhopper decisions: ``log(V) / log(B)``; the base is required (Grasshopper has no
        default); a non-positive number, or a base that is not positive or equals 1, raises
        ``ValueError`` (Grasshopper emits NaN).
    """

    display_name = "Log N"
    nickname = "LogN"
    gh_guid = "7ab8d289-26a2-4dd4-b4ad-df5b477999d8"

    inputs = [
        InputParam("number", float, Access.ITEM, default=0.0),
        InputParam("base", float, Access.ITEM),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, number=0.0, base=None):
        x, b = float(number), float(base)
        if x <= 0.0:
            raise ValueError("LogN requires a positive number")
        if b <= 0.0 or b == 1.0:
            raise ValueError("LogN requires a positive base other than 1")
        return math.log(x) / math.log(b)
