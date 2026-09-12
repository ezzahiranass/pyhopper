"""DivideDomain2 - Divides a two-dimensional domain into equal segments (Grasshopper "Divide Domain²")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicInterval2
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DivideDomain2(Component):
    """Divides a two-dimensional domain into equal segments.

    Inputs:
        domain: Base domain (Grasshopper Domain [item]).
        u_count: Number of segments in {u} direction (Grasshopper U Count [item]).
        v_count: Number of segments in {v} direction (Grasshopper V Count [item]).

    Outputs:
        segments: Individual segments (Grasshopper Segments).

    Notes:
        Grasshopper: Maths > Domain > Divide Domain² (Divide).
        pyhopper decisions: Grasshopper-verified — the segments come U-major (all V segments of the
        first U segment, then the next U segment …) as one list, the last bound landing exactly on the
        domain end; a zero count gives an empty list and negative counts raise ``ValueError``.
        Grasshopper defaults 10 x 10.
    """

    display_name = "Divide Domain²"
    nickname = "Divide"
    gh_guid = "75ac008b-1bc2-4edd-b967-667d628b9d24"

    inputs = [
        InputParam("domain", AtomicInterval2, Access.ITEM, default=AtomicInterval2()),
        InputParam("u_count", int, Access.ITEM, default=10),
        InputParam("v_count", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("segments", AtomicInterval2, access=Access.LIST),
    ]

    def generate(self, domain=AtomicInterval2(), u_count=10, v_count=10):
        u_segments, v_segments = int(u_count), int(v_count)
        if u_segments < 0 or v_segments < 0:
            raise ValueError("DivideDomain2 needs non-negative segment counts")

        def bounds(interval, count):
            start, end = float(interval.start), float(interval.end)
            values = [start + (end - start) * index / count for index in range(count)] + [end]
            return list(zip(values, values[1:]))

        return [AtomicInterval2(AtomicInterval(u0, u1), AtomicInterval(v0, v1)) for u0, u1 in bounds(domain.u, u_segments) for v0, v1 in bounds(domain.v, v_segments)] if u_segments and v_segments else []
