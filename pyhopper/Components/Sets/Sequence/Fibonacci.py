"""Fibonacci - Creates a Fibonacci sequence (Grasshopper "Fibonacci")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Fibonacci(Component):
    """Creates a Fibonacci sequence.

    Inputs:
        seed_a: First seed number of the sequence (Grasshopper Seed A [item]).
        seed_b: Second seed number of the sequence (Grasshopper Seed B [item]).
        number: Number of values in the sequence (Grasshopper Number [item]).

    Outputs:
        series: First N numbers in this Fibonacci sequence (Grasshopper Series).

    Notes:
        Grasshopper: Sets > Sequence > Fibonacci (Fib).
        pyhopper decisions: Grasshopper-verified — the series holds the two seeds followed by
        ``number`` further terms (N = 10 gives 12 values), and N = 0 gives an empty list; a negative
        N raises ``ValueError``. Defaults 0, 1, 10 as in Grasshopper.
    """

    display_name = "Fibonacci"
    nickname = "Fib"
    gh_guid = "fe99f302-3d0d-4389-8494-bd53f7935a02"

    inputs = [
        InputParam("seed_a", float, Access.ITEM, default=0.0),
        InputParam("seed_b", float, Access.ITEM, default=1.0),
        InputParam("number", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("series", float, access=Access.LIST),
    ]

    def generate(self, seed_a=0.0, seed_b=1.0, number=10):
        count = int(number)
        if count < 0:
            raise ValueError("Fibonacci cannot have a negative length")
        if count == 0:
            return []
        series = [float(seed_a), float(seed_b)]
        for _ in range(count):
            series.append(series[-1] + series[-2])
        return series
