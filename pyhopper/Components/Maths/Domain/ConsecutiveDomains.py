"""ConsecutiveDomains - Create consecutive domains from a list of numbers (Grasshopper "Consecutive Domains")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from itertools import accumulate


class ConsecutiveDomains(Component):
    """Create consecutive domains from a list of numbers.

    Inputs:
        numbers: Numbers for consecutive domains (Grasshopper Numbers [list]).
        additive: If True, values are added to a sum-total (Grasshopper Additive [item]).

    Outputs:
        domains: Domains describing the spaces between the numbers (Grasshopper Domains).

    Notes:
        Grasshopper: Maths > Domain > Consecutive Domains (Consec).
        pyhopper decisions: Grasshopper-verified — additive (the default) chains the running sums
        ``[n0, n0+n1], [n0+n1, n0+n1+n2], …``; otherwise consecutive pairs ``[n0, n1], [n1, n2], …``
        in list order (decreasing domains are kept). Fewer than two numbers give an empty list.
    """

    display_name = "Consecutive Domains"
    nickname = "Consec"
    gh_guid = "95992b33-89e1-4d36-bd35-2754a11af21e"

    inputs = [
        InputParam("numbers", float, Access.LIST, default=[0.0, 0.5, 1.0, 1.5, 2.0]),
        InputParam("additive", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("domains", AtomicInterval, access=Access.LIST),
    ]

    def generate(self, numbers=None, additive=True):
        values = [float(number) for number in (numbers if numbers is not None else [0.0, 0.5, 1.0, 1.5, 2.0])]
        if additive:
            bounds = list(accumulate(values))
        else:
            bounds = values
        return [AtomicInterval(bounds[index], bounds[index + 1]) for index in range(len(bounds) - 1)]
