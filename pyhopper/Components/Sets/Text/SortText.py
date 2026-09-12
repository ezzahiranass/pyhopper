"""SortText - Sort a collection of text fragments (Grasshopper "Sort Text")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Text import invariant_sort_key


class SortText(Component):
    """Sort a collection of text fragments.

    Inputs:
        keys: Text fragments to sort (sorting key) (Grasshopper Keys [list]).
        values: Optional values to sort synchronously (Grasshopper Values [list]).
        culture: Cultural sorting rules (Grasshopper Culture [item]).

    Outputs:
        keys: Sorted text fragments (Grasshopper Keys).
        values: Sorted values (Grasshopper Values).

    Notes:
        Grasshopper: Sets > Text > Sort Text (TSort).
        pyhopper decisions: an approximation of .NET's invariant-culture ordering (verified on
        Grasshopper): accents and case are ignored first, then accented letters sort after their
        base letter, then lowercase before uppercase; digits sort before letters as text
        (``"10" < "9"``). ``culture`` is accepted but only the invariant culture is implemented.
        Values reorder with their keys and must match the key count (``ValueError`` otherwise);
        without values the second output is empty.
    """

    display_name = "Sort Text"
    nickname = "TSort"
    gh_guid = "cec16c67-7b8b-41f7-a5a5-f675177e524b"

    inputs = [
        InputParam("keys", str, Access.LIST),
        InputParam("values", None, Access.LIST, optional=True),
        InputParam("culture", str, Access.ITEM, default="invariant"),
    ]
    outputs = [
        OutputParam("keys", str, access=Access.LIST),
        OutputParam("values", access=Access.LIST),
    ]

    def generate(self, keys=None, values=None, culture="invariant"):
        texts = [str(key) for key in (keys or [])]
        order = sorted(range(len(texts)), key=lambda index: invariant_sort_key(texts[index]))
        if values is None:
            return [texts[index] for index in order], []
        payload = list(values)
        if len(payload) != len(texts):
            raise ValueError("SortText needs one value per key")
        return [texts[index] for index in order], [payload[index] for index in order]
