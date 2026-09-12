"""StreamFilter - Filters a collection of input streams (Grasshopper "Stream Filter")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import builtins

from pyhopper.Core.DataTree import DataTree


class StreamFilter(Component):
    """Filters a collection of input streams.

    Inputs:
        gate: Index of Gate stream (Grasshopper Gate [item]).
        streams: Input stream at index 0 (Grasshopper Stream 0 / Stream 1 [tree]).

    Outputs:
        stream: Filtered stream (Grasshopper Stream).

    Notes:
        Grasshopper: Sets > Tree > Stream Filter (Filter).
        pyhopper decisions: ``gate`` picks one of the streams (0-based); an index outside the
        streams raises ``IndexError`` where Grasshopper emits nothing with an error; with no
        streams wired the output is empty. Several gate
        values produce the union of the selected streams (Grasshopper uses only the first).
    """

    display_name = "Stream Filter"
    nickname = "Filter"
    gh_guid = "eeafc956-268e-461d-8e73-ee05c6f72c01"

    inputs = [
        InputParam("gate", int, Access.ITEM, default=0),
        InputParam("streams", None, Access.TREE, optional=True),
    ]
    outputs = [
        OutputParam("stream", access=Access.TREE),
    ]
    variadic_inputs = True

    def generate(self, gate=0, streams=None):
        available = builtins.list(streams or [])
        if not available:
            return DataTree()  # nothing wired, nothing to pick
        index = int(gate)
        if not 0 <= index < len(available):
            raise IndexError(f"StreamFilter gate {index} is out of range for {len(available)} streams")
        return available[index]
