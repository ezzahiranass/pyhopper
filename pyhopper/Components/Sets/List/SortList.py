"""SortList - Sort a list of numeric keys (Grasshopper "Sort List")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class SortList(Component):
    """Sort a list of numeric keys.

    Inputs:
        keys: List of sortable keys (Grasshopper Keys [list]).
        values: Optional list of values to sort synchronously (Grasshopper Values A [list]).

    Outputs:
        keys: Sorted keys (Grasshopper Keys).
        values: Synchronous values in A (Grasshopper Values A).

    Notes:
        Grasshopper: Sets > List > Sort List (Sort).
        pyhopper decisions: keys sort ascending with a stable sort (equal keys keep their order); one value
        stream is sorted alongside and must match the key count (Grasshopper refuses
        mismatched lengths); more than one stream raises ``TypeError`` until pyhopper
        has variadic outputs.
    """

    display_name = "Sort List"
    nickname = "Sort"
    gh_guid = "6f93d366-919f-4dda-a35e-ba03dd62799b"

    inputs = [
        InputParam("keys", float, Access.LIST),
        InputParam("values", None, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("keys", float, access=Access.LIST),
        OutputParam("values", access=Access.LIST),
    ]
    variadic_inputs = True

    def generate(self, keys=None, values=()):
        sort_keys = [float(key) for key in (keys or [])]
        order = sorted(range(len(sort_keys)), key=lambda index: sort_keys[index])
        sorted_keys = [sort_keys[index] for index in order]
        streams = [builtins.list(stream) for stream in (values or [])]
        if not streams:
            return sorted_keys, []
        if len(streams) > 1:
            raise TypeError("Sort List sorts one value stream per component until variadic outputs are available")
        stream = streams[0]
        if len(stream) != len(sort_keys):
            raise ValueError(f"Sort List needs as many values ({len(stream)}) as keys ({len(sort_keys)})")
        return sorted_keys, [stream[index] for index in order]
