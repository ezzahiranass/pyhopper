"""RegionUnion - Union closed planar curve regions."""

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Adapters.shapely_regions import region_union


class RegionUnion(Component):
    """Union a branch of planar closed curves and return result outlines.

    Curves are projected to the supplied plane before solving. Curved inputs
    are sampled into planar polygon boundaries for the Shapely operation, and
    the result is returned as closed ``AtomicPolyline`` outlines.
    """

    inputs = [
        InputParam("curves", CURVE, Access.LIST),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [OutputParam("result", CURVE, access=Access.LIST)]

    def generate(self, curves=None, plane=AtomicPlane.world_xy()):
        return region_union(curves or [], plane)
