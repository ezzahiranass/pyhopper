"""CullNth - Cull (remove) every Nth element in a list (Grasshopper "Cull Nth")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class CullNth(Component):
    """Cull (remove) every Nth element in a list.

    Inputs:
        list: List to cull (Grasshopper List [list]).
        cull_frequency: Cull frequency (Grasshopper Cull frequency [item]).

    Outputs:
        list: Culled list (Grasshopper List).

    Notes:
        Grasshopper: Sets > Sequence > Cull Nth (CullN).
        pyhopper decisions: removes every N-th item (positions N-1, 2N-1, ...); a frequency below 2 raises
        ``ValueError`` (Grasshopper reports an error). Grasshopper default ``2``.
    """

    display_name = "Cull Nth"
    nickname = "CullN"
    gh_guid = "932b9817-fcc6-4ac3-b5fd-c0e8eeadc53f"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("cull_frequency", int, Access.ITEM, default=2),
    ]
    outputs = [
        OutputParam("list", access=Access.LIST),
    ]

    def generate(self, list=None, cull_frequency=2):
        frequency = int(cull_frequency)
        if frequency < 2:
            raise ValueError("Cull Nth frequency must be at least 2")
        return [item for index, item in enumerate(list or []) if (index + 1) % frequency != 0]
