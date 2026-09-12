"""SegmentLengths - Finds the shortest and longest segments of a curve (Grasshopper "Segment Lengths")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_segments
from pyhopper.Core.TypeSystem import CURVE


class SegmentLengths(Component):
    """Finds the shortest and longest segments of a curve.

    Inputs:
        curve: Curve to measure (Grasshopper Curve [item]).

    Outputs:
        shortest_length: Length of shortest segment (Grasshopper Shortest Length).
        shortest_domain: Curve domain of shortest segment (Grasshopper Shortest Domain).
        longest_length: Length of longest segment (Grasshopper Longest Length).
        longest_domain: Curve domain of longest segment (Grasshopper Longest Domain).

    Notes:
        Grasshopper: Curve > Analysis > Segment Lengths (LenSeg).
        pyhopper decisions: polylines are examined edge by edge (domains in the polyline's uniform
        per-edge parameterisation); any other curve is one segment spanning its whole domain — as
        Grasshopper reports for curves without a polycurve structure. Ties keep the first segment.
    """

    display_name = "Segment Lengths"
    nickname = "LenSeg"
    gh_guid = "f88a6cd9-1035-4361-b896-4f2dfe79272d"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("shortest_length", float),
        OutputParam("shortest_domain", AtomicInterval),
        OutputParam("longest_length", float),
        OutputParam("longest_domain", AtomicInterval),
    ]

    def generate(self, curve=None):
        segments = curve_segments(curve)
        shortest = min(segments, key=lambda segment: segment[2])
        longest = max(segments, key=lambda segment: segment[2])
        return shortest[2], AtomicInterval(shortest[0], shortest[1]), longest[2], AtomicInterval(longest[0], longest[1])
