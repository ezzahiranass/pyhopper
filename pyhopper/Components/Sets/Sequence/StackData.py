"""StackData - Duplicate individual items in a list of data (Grasshopper "Stack Data")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._lists import cycle


class StackData(Component):
    """Duplicate individual items in a list of data.

    Inputs:
        data: Data to stack (Grasshopper Data [list]).
        stack: Stacking pattern (Grasshopper Stack [list]).

    Outputs:
        data: Stacked data (Grasshopper Data).

    Notes:
        Grasshopper: Sets > Sequence > Stack Data (Stack).
        pyhopper decisions: item ``i`` repeats ``stack[i]`` times, the stack pattern cycling to the
        data length (Grasshopper-verified: ``[2, 0]`` on four items keeps items 0 and 2 twice);
        negative counts stack nothing; an empty stack stacks nothing.
    """

    display_name = "Stack Data"
    nickname = "Stack"
    gh_guid = "5fa4e736-0d82-4af0-97fb-30a79f4cbf41"

    inputs = [
        InputParam("data", None, Access.LIST, default=["A", "B", "C", "D"]),
        InputParam("stack", int, Access.LIST, default=[1, 2, 3, 4]),
    ]
    outputs = [
        OutputParam("data", access=Access.LIST),
    ]

    def generate(self, data=None, stack=None):
        items = list(data if data is not None else ["A", "B", "C", "D"])
        counts = [int(count) for count in (stack if stack is not None else [1, 2, 3, 4])]
        result = []
        for item, count in zip(items, cycle(counts, len(items))):
            result.extend([item] * max(count, 0))
        return result
