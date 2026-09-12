"""TrimWithRegions - Trim a curve with multiple regions (Grasshopper "Trim with Regions")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import trim_with_regions


class TrimWithRegions(Component):
    """Trim a curve with multiple regions.

    Inputs:
        curve: Curve to trim (Grasshopper Curve [item]).
        regions: Regions to trim against (Grasshopper Regions [list]).
        plane: Optional solution plane. If omitted the curve best-fit plane is used. (Grasshopper Plane [item]).

    Outputs:
        inside: Split curves inside the regions (Grasshopper Inside).
        outside: Split curves outside the regions (Grasshopper Outside).

    Notes:
        Grasshopper: Intersect > Region > Trim with Regions (Trim).
        pyhopper decisions: Grasshopper-verified — the curve is split where its projection onto the
        solution plane crosses any region (touches included); a piece is inside when its midpoint
        projects inside or onto at least one region (a coincident midpoint counts as inside, as in
        Grasshopper). Without a plane the first region's plane is used (Grasshopper fits one to the
        curve, which for the usual planar set-ups is the same plane). Open regions raise ``ValueError``
        with Grasshopper's message. Coincidence uses pyhopper's absolute tolerance (0.01, Rhino's default
        document tolerance that Grasshopper uses).
    """

    display_name = "Trim with Regions"
    nickname = "Trim"
    gh_guid = "26949c81-9b50-43b7-ac49-3203deb6eec7"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("regions", CURVE, Access.LIST),
        InputParam("plane", AtomicPlane, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("inside", CURVE, access=Access.LIST),
        OutputParam("outside", CURVE, access=Access.LIST),
    ]

    def generate(self, curve=None, regions=None, plane=None):
        inside, outside = trim_with_regions(curve, regions or [], plane)
        return inside, outside
