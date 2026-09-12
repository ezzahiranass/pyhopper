"""Weave - Weave a set of input data using a custom pattern (Grasshopper "Weave")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Weave(Component):
    """Weave a set of input data using a custom pattern.

    Inputs:
        pattern: Weave pattern of input indices (Grasshopper Pattern [list]).
        streams: Input stream  0 (Grasshopper Stream 0 / Stream 1 [list]).

    Outputs:
        weave: Weave result (Grasshopper Weave).

    Notes:
        Grasshopper: Sets > List > Weave (Weave).
        pyhopper decisions: the pattern repeats until every stream is consumed; exhausted streams are
        skipped (Grasshopper behaviour); a pattern index with no stream raises
        ``ValueError`` where Grasshopper skips it with a warning.
    """

    display_name = "Weave"
    nickname = "Weave"
    gh_guid = "50faccbd-9c92-4175-a5fa-d65e36013db6"

    inputs = [
        InputParam("pattern", int, Access.LIST, default=[0, 1]),
        InputParam("streams", None, Access.LIST),
    ]
    outputs = [
        OutputParam("weave", access=Access.LIST),
    ]
    variadic_inputs = True

    def generate(self, pattern=(0, 1), streams=()):
        sequence = [int(index) for index in (pattern or [])]
        sources = [builtins.list(stream) for stream in (streams or [])]
        if not sequence or not sources:
            return []
        for index in sequence:
            if not 0 <= index < len(sources):
                raise ValueError(f"Weave pattern index {index} has no stream (0 <= i < {len(sources)})")
        cursors = [0] * len(sources)
        woven = []
        referenced = set(sequence)
        while any(cursors[index] < len(sources[index]) for index in referenced):
            for index in sequence:
                if cursors[index] < len(sources[index]):
                    woven.append(sources[index][cursors[index]])
                    cursors[index] += 1
        return woven
