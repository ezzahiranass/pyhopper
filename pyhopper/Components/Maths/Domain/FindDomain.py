"""FindDomain - Find the first domain that contains a specific value (Grasshopper "Find Domain")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class FindDomain(Component):
    """Find the first domain that contains a specific value.

    Inputs:
        domains: Collection of domains to search (Grasshopper Domains [list]).
        number: Number to test (Grasshopper Number [item]).
        strict: Strict comparison, if true then the value must be on the interior of a domain (Grasshopper Strict [item]).

    Outputs:
        index: Index of first domain that includes the specified value (Grasshopper Index).
        neighbour: Index of domain that is closest to the specified value (Grasshopper Neighbour).

    Notes:
        Grasshopper: Maths > Domain > Find Domain (FDom).
        pyhopper decisions: Grasshopper-verified — ``index`` is the first domain containing the
        number (bounds inclusive unless strict; a decreasing domain counts by its min/max), -1 when
        none does; ``neighbour`` is the first domain at minimum distance (0 inside). An empty
        domain list emits nothing.
    """

    display_name = "Find Domain"
    nickname = "FDom"
    gh_guid = "0b5c7fad-0473-41aa-bf52-d7a861dcaa29"

    inputs = [
        InputParam("domains", AtomicInterval, Access.LIST),
        InputParam("number", float, Access.ITEM),
        InputParam("strict", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("index", int),
        OutputParam("neighbour", int),
    ]

    def generate(self, domains=None, number=None, strict=False):
        intervals = list(domains or [])
        if not intervals:
            return Component.NO_OUTPUT, Component.NO_OUTPUT
        value = float(number)
        index = -1
        nearest, best = 0, math.inf
        for position, interval in enumerate(intervals):
            low, high = min(interval.start, interval.end), max(interval.start, interval.end)
            inside = low < value < high if strict else low <= value <= high
            if inside and index < 0:
                index = position
            distance = 0.0 if low <= value <= high else min(abs(value - low), abs(value - high))
            if distance < best:
                nearest, best = position, distance
        return index, nearest
