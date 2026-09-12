"""StreamGate - Redirects a stream into specific outputs (Grasshopper "Stream Gate")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class StreamGate(Component):
    """Redirects a stream into specific outputs.

    Inputs:
        stream: Input stream (Grasshopper Stream [tree]).
        gate: Gate index of output stream (Grasshopper Gate [item]).

    Outputs:
        target_0: Output for Gate index 0 (Grasshopper Target 0).
        target_1: Output for Gate index 1 (Grasshopper Target 1).

    Notes:
        Grasshopper: Sets > Tree > Stream Gate (Gate).
        pyhopper decisions: the stream goes to ``target_<gate>`` and the other target stays empty;
        Grasshopper's ZUI adds targets on demand, pyhopper offers the two default ones; a gate
        outside them raises ``IndexError`` where Grasshopper emits nothing with an error.
    """

    display_name = "Stream Gate"
    nickname = "Gate"
    gh_guid = "71fcc052-6add-4d70-8d97-cfb37ea9d169"

    inputs = [
        InputParam("stream", None, Access.TREE),
        InputParam("gate", int, Access.ITEM, default=0),
    ]
    outputs = [
        OutputParam("target_0", access=Access.TREE),
        OutputParam("target_1", access=Access.TREE),
    ]

    def generate(self, stream=None, gate=0):
        source = DataTree() if stream is None else stream
        index = int(gate)
        if index == 0:
            return source, DataTree()
        if index == 1:
            return DataTree(), source
        raise IndexError(f"StreamGate gate {index} is out of range for 2 targets")
