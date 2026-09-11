"""LinePlane - Solve intersection event for a line and a plane (Grasshopper "Line | Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._closed_form import line_plane_intersection


class LinePlane(Component):
    """Solve intersection event for a line and a plane.

    Inputs:
        line: Base line (Grasshopper Line [item]).
        plane: Intersection plane (Grasshopper Plane [item]).

    Outputs:
        point: Intersection event (Grasshopper Point).
        param_l: Parameter {t} on infinite line (Grasshopper Param L).
        param_p: Parameter {uv} on plane (Grasshopper Param P).

    Notes:
        Grasshopper: Intersect > Mathematical > Line | Plane (PLX).
        pyhopper decisions: the line is infinite (``param_l`` beyond 0..1 outside the segment); ``param_p`` is the
        intersection in plane coordinates as a point; a line parallel to the plane emits nothing.
    """

    display_name = "Line | Plane"
    nickname = "PLX"
    gh_guid = "75d0442c-1aa3-47cf-bd94-457b42c16e9f"

    inputs = [
        InputParam("line", AtomicLine, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("param_l", float),
        OutputParam("param_p", AtomicPoint),
    ]

    def generate(self, line=None, plane=AtomicPlane.world_xy()):
        result = line_plane_intersection(line, plane)
        return (Component.NO_OUTPUT, Component.NO_OUTPUT, Component.NO_OUTPUT) if result is None else result
