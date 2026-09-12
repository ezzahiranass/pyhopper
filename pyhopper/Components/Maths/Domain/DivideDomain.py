"""DivideDomain - Divide a domain into equal segments (Grasshopper "Divide Domain")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DivideDomain(Component):
    """Divide a domain into equal segments.

    Inputs:
        domain: Base domain (Grasshopper Domain [item]).
        count: Number of segments (Grasshopper Count [item]).

    Outputs:
        segments: Division segments (Grasshopper Segments).

    Notes:
        Grasshopper: Maths > Domain > Divide Domain (Div).
        pyhopper decisions: ``count`` below one raises ``ValueError`` (Grasshopper emits an empty branch);
        the last segment ends exactly at the domain end. Segments follow the base-class list rule
        (sub-branch only when a branch runs several iterations) where Grasshopper always emits
        ``{path;iteration}``.
    """

    display_name = "Divide Domain"
    nickname = "Div"
    gh_guid = "75ef4190-91a2-42d9-a245-32a7162b0384"

    inputs = [
        InputParam("domain", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
        InputParam("count", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("segments", AtomicInterval),
    ]

    def generate(self, domain=AtomicInterval(0.0, 1.0), count=10):
        segments = int(count)
        if segments < 1:
            raise ValueError("DivideDomain requires a positive segment count")
        start, end = float(domain.start), float(domain.end)
        bounds = [start + (end - start) * index / segments for index in range(segments + 1)]
        bounds[-1] = end
        return [AtomicInterval(a, b) for a, b in zip(bounds, bounds[1:])]
