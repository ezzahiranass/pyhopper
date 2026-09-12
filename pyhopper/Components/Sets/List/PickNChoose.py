"""PickNChoose - Pick and choose from a set of input data (Grasshopper "Pick'n'Choose")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class PickNChoose(Component):
    """Pick and choose from a set of input data.

    Inputs:
        pattern: Pick pattern of input indices (Grasshopper Pattern [list]).
        streams: Input stream 0 (Grasshopper Stream 0 / Stream 1 [list]).

    Outputs:
        result: Picked result (Grasshopper Result).

    Notes:
        Grasshopper: Sets > List > Pick'n'Choose (P'n'C).
        pyhopper decisions: Grasshopper-verified — the result has one item per pattern entry (the
        pattern does not repeat), taken from stream ``pattern[i]`` at position ``i``; a stream that is
        too short contributes ``None`` and a pattern index without a stream is skipped (Grasshopper
        warns in both cases). Default pattern ``[0, 1]``.
    """

    display_name = "Pick'n'Choose"
    nickname = "P'n'C"
    gh_guid = "03b801eb-87cd-476a-a591-257fe5d5bf0f"

    inputs = [
        InputParam("pattern", int, Access.LIST, default=[0, 1]),
        InputParam("streams", None, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("result", access=Access.LIST),
    ]
    variadic_inputs = True

    def generate(self, pattern=(0, 1), streams=()):
        sources = [list(stream) for stream in (streams or [])]
        picked = []
        for position, index in enumerate(int(value) for value in (pattern or [])):
            if not 0 <= index < len(sources):
                continue
            stream = sources[index]
            picked.append(stream[position] if position < len(stream) else None)
        return picked
