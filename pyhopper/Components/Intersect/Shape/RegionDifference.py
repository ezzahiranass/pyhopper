"""RegionDifference - Subtract closed planar curve regions."""

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Adapters.shapely_regions import region_difference


def _branch_plane(planes) -> AtomicPlane:
    return planes[0] if planes else AtomicPlane.world_xy()


class RegionDifference(Component):
    """Subtract one branch of planar closed curve regions from another.

    Curves are projected to the supplied plane before solving. Curved inputs
    are sampled into planar polygon boundaries for the Shapely operation, and
    the result is returned as closed ``AtomicPolyline`` outlines.
    """

    inputs = [
        InputParam("curves_a", CURVE, Access.LIST),
        InputParam("curves_b", CURVE, Access.LIST),
        InputParam("plane", AtomicPlane, Access.LIST, default=AtomicPlane.world_xy()),
    ]
    outputs = [OutputParam("result", CURVE)]

    def generate(self, curves_a=None, curves_b=None, plane=None):
        return region_difference(curves_a or [], curves_b or [], _branch_plane(plane))
