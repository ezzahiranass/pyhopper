"""ModifiedArc - Create an arc based on another arc (Grasshopper "Modified Arc")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicArc, AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ModifiedArc(Component):
    """Create an arc based on another arc.

    Inputs:
        arc: Base arc (Grasshopper Arc [item]).
        radius: Optional new radius (Grasshopper Radius [item]).
        angle: Optional new angle domain (Grasshopper Angle [item]).

    Outputs:
        arc: Modified arc (Grasshopper Arc).

    Notes:
        Grasshopper: Curve > Primitive > Modified Arc (ModArc).
        pyhopper decisions: none; a radius or angle domain that is not supplied keeps the arc's own value, as in Grasshopper.
    """

    display_name = "Modified Arc"
    nickname = "ModArc"
    gh_guid = "9d8dec9c-3fd1-481c-9c3d-75ea5e15eb1a"

    inputs = [
        InputParam("arc", AtomicArc, Access.ITEM),
        InputParam("radius", float, Access.ITEM, optional=True),
        InputParam("angle", AtomicInterval, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("arc", AtomicArc),
    ]

    def generate(self, arc=None, radius=None, angle=None):
        return AtomicArc(arc.plane, float(arc.radius if radius is None else radius), arc.angle if angle is None else angle)
