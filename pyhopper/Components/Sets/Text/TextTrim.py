"""TextTrim - Remove whitespace characters from the start and end of some text (Grasshopper "Text Trim")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class TextTrim(Component):
    """Remove whitespace characters from the start and end of some text.

    Inputs:
        text: Text to split. (Grasshopper Text [item]).
        start: Trim whitespace at start. (Grasshopper Start [item]).
        end: Trim whitespace at end. (Grasshopper End [item]).

    Outputs:
        result: Trimmed text. (Grasshopper Result).

    Notes:
        Grasshopper: Sets > Text > Text Trim (Trim).
        pyhopper decisions: removes leading and/or trailing whitespace (spaces, tabs, line breaks);
        Grasshopper defaults ``start = True``, ``end = True``.
    """

    display_name = "Text Trim"
    nickname = "Trim"
    gh_guid = "e4cb7168-5e32-4c54-b425-5a31c6fd685a"

    inputs = [
        InputParam("text", str, Access.ITEM, default=""),
        InputParam("start", bool, Access.ITEM, default=True),
        InputParam("end", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("result", str),
    ]

    def generate(self, text="", start=True, end=True):
        result = str(text)
        if start:
            result = result.lstrip()
        if end:
            result = result.rstrip()
        return result
