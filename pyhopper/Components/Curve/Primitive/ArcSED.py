"""ArcSED - Create an arc defined by start point, end point and a tangent vector (Grasshopper "Arc SED")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Arcs import arc_from_start_end_direction
from pyhopper.Core.TypeSystem import GEOMETRY


class ArcSED(Component):
    """Create an arc defined by start point, end point and a tangent vector.

    Inputs:
        start: Start point of arc (Grasshopper Start [item]).
        end: End point of arc (Grasshopper End [item]).
        direction: Direction (tangent) at start (Grasshopper Direction [item]).

    Outputs:
        arc: Resulting arc (Grasshopper Arc).
        plane: Arc plane (Grasshopper Plane).
        radius: Arc radius (Grasshopper Radius).

    Notes:
        Grasshopper: Curve > Primitive > Arc SED (Arc).
        pyhopper decisions: the arc is tangent to ``direction`` at the start, the plane sits at the centre with X
        towards the start; a direction along the chord (or zero) gives the chord as a line with an
        infinite radius, like Grasshopper.
    """

    display_name = "Arc SED"
    nickname = "Arc"
    gh_guid = "9d2583dd-6cf5-497c-8c40-c9a290598396"

    inputs = [
        InputParam("start", AtomicPoint, Access.ITEM),
        InputParam("end", AtomicPoint, Access.ITEM),
        InputParam("direction", AtomicVector, Access.ITEM),
    ]
    outputs = [
        OutputParam("arc", GEOMETRY),
        OutputParam("plane", AtomicPlane),
        OutputParam("radius", float),
    ]

    def generate(self, start=None, end=None, direction=None):
        return arc_from_start_end_direction(start, end, direction)
