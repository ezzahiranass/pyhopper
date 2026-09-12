"""RemapNumbers - Remap numbers into a new numeric domain (Grasshopper "Remap Numbers")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class RemapNumbers(Component):
    """Remap numbers into a new numeric domain.

    Inputs:
        value: Value to remap (Grasshopper Value [item]).
        source: Source domain (Grasshopper Source [item]).
        target: Target domain (Grasshopper Target [item]).

    Outputs:
        mapped: Remapped number (Grasshopper Mapped).
        clipped: Remapped and clipped number (Grasshopper Clipped).

    Notes:
        Grasshopper: Maths > Domain > Remap Numbers (ReMap).
        pyhopper decisions: ``mapped`` extrapolates outside the source domain, ``clipped`` clamps into it
        first; a zero-length source domain raises ``ValueError`` (Grasshopper maps it to the target
        midpoint and emits a null for ``clipped``).
    """

    display_name = "Remap Numbers"
    nickname = "ReMap"
    gh_guid = "2fcc2743-8339-4cdf-a046-a1f17439191d"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
        InputParam("source", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
        InputParam("target", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
    ]
    outputs = [
        OutputParam("mapped", float),
        OutputParam("clipped", float),
    ]

    def generate(self, value=0.0, source=AtomicInterval(0.0, 1.0), target=AtomicInterval(0.0, 1.0)):
        span = float(source.end) - float(source.start)
        if abs(span) <= 1e-12:
            raise ValueError("RemapNumbers requires a source domain with non-zero length")
        x = float(value)
        low, high = sorted((float(source.start), float(source.end)))
        factor = (x - float(source.start)) / span
        clipped_factor = (min(high, max(low, x)) - float(source.start)) / span
        return target.remap(factor), target.remap(clipped_factor)
