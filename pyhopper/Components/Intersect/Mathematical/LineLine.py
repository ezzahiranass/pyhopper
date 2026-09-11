"""LineLine - Solve intersection events for two lines (Grasshopper "Line | Line")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._closed_form import line_line_closest_points


class LineLine(Component):
    """Solve intersection events for two lines.

    Inputs:
        line_1: First line for intersection (Grasshopper Line 1 [item]).
        line_2: Second line for intersection (Grasshopper Line 2 [item]).

    Outputs:
        param_a: Parameter on line A (Grasshopper Param A).
        param_b: Parameter on line B (Grasshopper Param B).
        point_a: Point on line A (Grasshopper Point A).
        point_b: Point on line B (Grasshopper Point B).

    Notes:
        Grasshopper: Intersect > Mathematical > Line | Line (LLX).
        pyhopper decisions: lines are infinite, parameters normalised along each segment (beyond 0..1 outside it);
        skew lines give their closest points; (anti)parallel lines emit nothing (Grasshopper nulls).
    """

    display_name = "Line | Line"
    nickname = "LLX"
    gh_guid = "6d4b82a7-8c1d-4bec-af7b-ca321ba4beb1"

    inputs = [
        InputParam("line_1", AtomicLine, Access.ITEM),
        InputParam("line_2", AtomicLine, Access.ITEM),
    ]
    outputs = [
        OutputParam("param_a", float),
        OutputParam("param_b", float),
        OutputParam("point_a", AtomicPoint),
        OutputParam("point_b", AtomicPoint),
    ]

    def generate(self, line_1=None, line_2=None):
        result = line_line_closest_points(line_1, line_2)
        return (Component.NO_OUTPUT, Component.NO_OUTPUT, Component.NO_OUTPUT, Component.NO_OUTPUT) if result is None else result
