"""PlaneRegion - Create a bounded region from intersecting planes (Grasshopper "Plane Region")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import plane_region


class PlaneRegion(Component):
    """Create a bounded region from intersecting planes.

    Inputs:
        plane: Region plane and origin (Grasshopper Plane [item]).
        bounds: Region bounding planes (Grasshopper Bounds [list]).

    Outputs:
        region: Bounded region (Grasshopper Region).

    Notes:
        Grasshopper: Intersect > Mathematical > Plane Region (PlReg).
        pyhopper decisions: Grasshopper-verified — the cell of the plane around its origin cut out by
        the bounding planes (their orientation does not matter; bounds through the origin are ignored)
        as a closed polyline, clipped to a square of 10 units or twice the farthest bound; fewer than two
        effective bounds raise ``ValueError`` with Grasshopper's message. The polyline's seam follows
        the clipping order, where Rhino's is arbitrary.
    """

    display_name = "Plane Region"
    nickname = "PlReg"
    gh_guid = "80e3614a-25ae-43e7-bb0a-760e68ade864"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("bounds", AtomicPlane, Access.LIST),
    ]
    outputs = [
        OutputParam("region", CURVE),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), bounds=None):
        return plane_region(plane, bounds or [])
