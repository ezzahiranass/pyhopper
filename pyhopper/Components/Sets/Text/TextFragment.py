"""TextFragment - Extract a fragment (subset) of some text (Grasshopper "Text Fragment")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class TextFragment(Component):
    """Extract a fragment (subset) of some text.

    Inputs:
        text: Text to operate on. (Grasshopper Text [item]).
        start: Zero based index of first character to copy. (Grasshopper Start [item]).
        count: Optional number of characters to copy. If blank, the entire remainder will be copied. (Grasshopper Count [item]).

    Outputs:
        fragment: The resulting text fragment (Grasshopper Fragment).

    Notes:
        Grasshopper: Sets > Text > Text Fragment (Fragment).
        pyhopper decisions: ``text[start:start + count]`` (all of the rest when ``count`` is
        absent); a fragment running past the end is clipped and a start beyond the end gives an
        empty text, as in Grasshopper; a negative start raises ``ValueError`` (Grasshopper: null
        plus an error).
    """

    display_name = "Text Fragment"
    nickname = "Fragment"
    gh_guid = "07e0811f-034a-4504-bca0-2d03b2c46217"

    inputs = [
        InputParam("text", str, Access.ITEM, default=""),
        InputParam("start", int, Access.ITEM, default=0),
        InputParam("count", int, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("fragment", str),
    ]

    def generate(self, text="", start=0, count=None):
        source = str(text)
        begin = int(start)
        if begin < 0:
            raise ValueError("TextFragment start must be zero or positive")
        if count is None:
            return source[begin:]
        return source[begin: begin + max(int(count), 0)]
