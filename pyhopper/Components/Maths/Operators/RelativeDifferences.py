"""RelativeDifferences - Compute relative differences for a list of data (Grasshopper "Relative Differences")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicVector

from .._arith import Spatial, subtract


class RelativeDifferences(Component):
    """Compute relative differences for a list of data.

    Inputs:
        values: List of data to operate on (numbers or points or vectors allowed) (Grasshopper Values [list]).

    Outputs:
        differenced: Differences between consecutive items (Grasshopper Differenced).

    Notes:
        Grasshopper: Maths > Operators > Relative Differences (RelDif).
        pyhopper decisions: Grasshopper-verified — the result keeps the list length: a zero (or zero
        vector) first, then each item minus its predecessor; integers stay integers, points and vectors
        give vectors; an empty list stays empty. Mixed kinds raise ``TypeError`` (Grasshopper reports
        an error and emits nothing).
    """

    display_name = "Relative Differences"
    nickname = "RelDif"
    gh_guid = "dd17d442-3776-40b3-ad5b-5e188b56bd4c"

    inputs = [
        InputParam("values", None, Access.LIST),
    ]
    outputs = [
        OutputParam("differenced", access=Access.LIST),
    ]

    def generate(self, values=None):
        items = list(values or [])
        if not items:
            return []
        first = items[0]
        zero = AtomicVector(0.0, 0.0, 0.0) if isinstance(first, Spatial) else (0 if isinstance(first, int) and not isinstance(first, bool) else 0.0)
        return [zero] + [subtract(b, a, "RelativeDifferences") for a, b in zip(items, items[1:])]
