"""TrimWithRegion - Trim a curve with a region (Grasshopper "Trim with Region")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import trim_with_regions


class TrimWithRegion(Component):
    """Trim a curve with a region.

    Inputs:
        curve: Curve to trim (Grasshopper Curve [item]).
        region: Region to trim against (Grasshopper Region [item]).
        plane: Optional solution plane. If omitted the curve best-fit plane is used. (Grasshopper Plane [item]).

    Outputs:
        inside: Split curves inside the region (Grasshopper Inside).
        outside: Split curves outside the region (Grasshopper Outside).

    Notes:
        Grasshopper: Intersect > Region > Trim with Region (Trim).
        pyhopper decisions: Grasshopper-verified — the curve is split where its projection onto the
        solution plane crosses the region (touches included); a piece is inside when its midpoint
        projects inside or onto the region (a coincident midpoint counts as inside, as in Grasshopper).
        Without a plane the region's own plane is used (Grasshopper fits one to the curve, which for the
        usual planar set-ups is the same plane). A closed curve keeps its seam inside the piece that
        runs through it (a two-segment polycurve). Open regions raise ``ValueError`` with Grasshopper's
        message. Coincidence uses pyhopper's absolute tolerance (0.01, Rhino's default document
        tolerance that Grasshopper uses).
    """

    display_name = "Trim with Region"
    nickname = "Trim"
    gh_guid = "3092caf0-7cf9-4885-bcc0-e635d878832a"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("region", CURVE, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("inside", CURVE, access=Access.LIST),
        OutputParam("outside", CURVE, access=Access.LIST),
    ]

    def generate(self, curve=None, region=None, plane=None):
        inside, outside = trim_with_regions(curve, [region], plane)
        return inside, outside
