"""DeconstructArc - Retrieve the base plane, radius and angle domain of an arc (Grasshopper "Deconstruct Arc")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicArc, AtomicInterval, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Arcs import arc_from_plane


class DeconstructArc(Component):
    """Retrieve the base plane, radius and angle domain of an arc.

    Inputs:
        arc: Arc or Circle to deconstruct (Grasshopper Arc [item]).

    Outputs:
        base_plane: Base plane of arc or circle (Grasshopper Base Plane).
        radius: Radius of arc or circle (Grasshopper Radius).
        angle: Angle domain (in radians) of arc (Grasshopper Angle).

    Notes:
        Grasshopper: Curve > Analysis > Deconstruct Arc (DArc).
        pyhopper decisions: an arc whose angle domain runs backwards is reported the way Grasshopper
        does — on the flipped plane with the negated, increasing domain.
    """

    display_name = "Deconstruct Arc"
    nickname = "DArc"
    gh_guid = "23862862-049a-40be-b558-2418aacbd916"

    inputs = [
        InputParam("arc", AtomicArc, Access.ITEM),
    ]
    outputs = [
        OutputParam("base_plane", AtomicPlane),
        OutputParam("radius", float),
        OutputParam("angle", AtomicInterval),
    ]

    def generate(self, arc=None):
        normalized = arc_from_plane(arc.plane, arc.radius, arc.angle)
        return normalized.plane, normalized.radius, normalized.angle
