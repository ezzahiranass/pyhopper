"""RandomReduce - Randomly remove N items from a list (Grasshopper "Random Reduce")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import builtins
import random


class RandomReduce(Component):
    """Randomly remove N items from a list.

    Inputs:
        list: List to reduce (Grasshopper List [list]).
        reduction: Number of items to remove (Grasshopper Reduction [item]).
        seed: Random Generator Seed value (Grasshopper Seed [item]).

    Outputs:
        list: Reduced list (Grasshopper List).

    Notes:
        Grasshopper: Sets > Sequence > Random Reduce (Reduce).
        pyhopper decisions: removes ``reduction`` items chosen by a seeded pseudo-random engine
        (a different sequence from Grasshopper, deterministic per seed) and keeps the survivors in
        their original order where Grasshopper shuffles them; removing everything or more gives an
        empty list; a negative reduction raises ``ValueError``. Seed default 1 as in Grasshopper.
    """

    display_name = "Random Reduce"
    nickname = "Reduce"
    gh_guid = "455925fd-23ff-4e57-a0e7-913a4165e659"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("reduction", int, Access.ITEM, default=0),
        InputParam("seed", int, Access.ITEM, default=1),
    ]
    outputs = [
        OutputParam("list", access=Access.LIST),
    ]

    def generate(self, list=None, reduction=0, seed=1):
        items = builtins.list(list or [])
        count = int(reduction)
        if count < 0:
            raise ValueError("RandomReduce reduction cannot be negative")
        if count >= len(items):
            return []
        doomed = set(random.Random(int(seed)).sample(range(len(items)), count))
        return [item for position, item in enumerate(items) if position not in doomed]
