"""TextDistance - Compute the Levenshtein distance between two fragments of text (Grasshopper "Text Distance")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Text import levenshtein


class TextDistance(Component):
    """Compute the Levenshtein distance between two fragments of text.

    Inputs:
        text_a: First text fragment (Grasshopper Text A [item]).
        text_b: Second text fragment (Grasshopper Text B [item]).
        case: Compare using case-sensitive matching (Grasshopper Case [item]).

    Outputs:
        distance: Levenshtein distance between the two fragments (Grasshopper Distance).

    Notes:
        Grasshopper: Sets > Text > Text Distance (TDist).
        pyhopper decisions: the Levenshtein edit distance; ``case`` (default True, as in Grasshopper)
        makes the comparison case-sensitive, otherwise both texts are lower-cased first.
    """

    display_name = "Text Distance"
    nickname = "TDist"
    gh_guid = "f7608c4d-836c-4adf-9d1f-3b04e6a2647d"

    inputs = [
        InputParam("text_a", str, Access.ITEM, default=""),
        InputParam("text_b", str, Access.ITEM, default=""),
        InputParam("case", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("distance", int),
    ]

    def generate(self, text_a="", text_b="", case=True):
        a, b = str(text_a), str(text_b)
        if not case:
            a, b = a.lower(), b.lower()
        return levenshtein(a, b)
