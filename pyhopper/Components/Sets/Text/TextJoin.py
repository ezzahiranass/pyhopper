"""TextJoin - Join a collection of text fragments into one (Grasshopper "Text Join")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class TextJoin(Component):
    """Join a collection of text fragments into one.

    Inputs:
        text: Text fragments to join. (Grasshopper Text [list]).
        join: Fragment separator. (Grasshopper Join [item]).

    Outputs:
        result: Resulting text (Grasshopper Result).

    Notes:
        Grasshopper: Sets > Text > Text Join (Join).
        pyhopper decisions: the separator defaults to an empty string, like Grasshopper; numbers arrive
        already formatted the Grasshopper way (``1.0`` -> ``1``) through the ``str`` port;
        an empty list emits nothing (Grasshopper emits a null).
    """

    display_name = "Text Join"
    nickname = "Join"
    gh_guid = "1274d51a-81e6-4ccf-ad1f-0edf4c769cac"

    inputs = [
        InputParam("text", str, Access.LIST),
        InputParam("join", str, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("result", str),
    ]

    def generate(self, text=None, join=None):
        fragments = builtins.list(text or [])
        if not fragments:
            return Component.NO_OUTPUT
        return ("" if join is None else str(join)).join(fragments)
