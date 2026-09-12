"""Maximum - Return the greater of two items (Grasshopper "Maximum")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Maximum(Component):
    """Return the greater of two items.

    Inputs:
        a: First item for comparison (Grasshopper A [item]).
        b: Second item for comparison (Grasshopper B [item]).

    Outputs:
        result: The greater of A and B (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Util > Maximum (Max).
        pyhopper decisions: numeric inputs only (Grasshopper evaluates text as expressions).
    """

    display_name = "Maximum"
    nickname = "Max"
    gh_guid = "0d1e2027-f153-460d-84c0-f9af431b08cb"

    inputs = [
        InputParam("a", float, Access.ITEM, default=0.0),
        InputParam("b", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, a=0.0, b=0.0):
        return max(float(a), float(b))
