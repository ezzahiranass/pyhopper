"""Random - Generate a deterministic list of pseudo-random numbers."""

import builtins
import random as _random

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Random(Component):
    """Generate pseudo-random numbers within a numeric range.

    Each matched ``range``, ``number``, and ``seed`` tuple creates one
    deterministic list. The inherited solve pipeline preserves DataTree
    matching and creates sub-branches when multiple lists are generated.
    """

    inputs = [
        InputParam("range", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
        InputParam("number", int, Access.ITEM, default=1),
        InputParam("seed", int, Access.ITEM, default=0),
    ]
    outputs = [OutputParam("random", float)]

    def generate(self, range=AtomicInterval(0.0, 1.0), number=1, seed=0):
        generator = _random.Random(int(seed))
        count = max(int(number), 0)
        return [
            range.start + generator.random() * (range.end - range.start)
            for _ in builtins.range(count)
        ]
