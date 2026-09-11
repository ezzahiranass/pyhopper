"""Jitter - Randomly shuffles a list of values (Grasshopper "Jitter")."""

from __future__ import annotations

import builtins
import random

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Jitter(Component):
    """Randomly shuffles a list of values.

    Inputs:
        list: Values to shuffle (Grasshopper List [list]).
        jitter: Shuffling strength. (0.0 = no shuffling, 1.0 = complete shuffling) (Grasshopper Jitter [item]).
        seed: Seed of shuffling engine (Grasshopper Seed [item]).

    Outputs:
        values: Shuffled values (Grasshopper Values).
        indices: Index map of shuffled items (Grasshopper Indices).

    Notes:
        Grasshopper: Sets > Sequence > Jitter (Jitter).
        pyhopper decisions: a seeded pseudo-random shuffle: each item moves by up to ``jitter``
        (clamped to 0..1) times the list length; ``0`` keeps the order, ``1`` shuffles
        fully. Deterministic per seed but a different sequence from Grasshopper;
        Grasshopper defaults ``jitter = 1.0``, ``seed = 2``.
    """

    display_name = "Jitter"
    nickname = "Jitter"
    gh_guid = "f02a20f6-bb49-4e3d-b155-8ed5d3c6b000"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("jitter", float, Access.ITEM, default=1.0),
        InputParam("seed", int, Access.ITEM, default=2),
    ]
    outputs = [
        OutputParam("values", access=Access.LIST),
        OutputParam("indices", int, access=Access.LIST),
    ]

    def generate(self, list=None, jitter=1.0, seed=2):
        items = builtins.list(list or [])
        strength = min(1.0, max(0.0, float(jitter)))
        count = len(items)
        if strength <= 0.0 or count < 2:
            return items, builtins.list(range(count))
        generator = random.Random(int(seed))
        positions = [index + generator.uniform(-strength, strength) * count for index in range(count)]
        order = sorted(range(count), key=lambda index: positions[index])
        return [items[index] for index in order], order
