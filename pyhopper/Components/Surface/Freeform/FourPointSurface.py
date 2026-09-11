"""FourPointSurface - Create a surface from three or four corner points."""

from pyhopper.Core.Atoms import AtomicPoint, AtomicSurface
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Surfaces import surface_from_corners


class FourPointSurface(Component):
    """Create a bilinear surface connecting three or four corner points.

    The first three corners are required. ``corner_d`` is optional; when it is
    omitted, the component creates a triangular degenerate bilinear patch.
    """

    inputs = [
        InputParam("corner_a", AtomicPoint, Access.ITEM),
        InputParam("corner_b", AtomicPoint, Access.ITEM),
        InputParam("corner_c", AtomicPoint, Access.ITEM),
        InputParam("corner_d", AtomicPoint, Access.ITEM, default=None, optional=True),
    ]
    outputs = [OutputParam("surface", AtomicSurface)]

    def generate(self, corner_a=None, corner_b=None, corner_c=None, corner_d=None):
        return surface_from_corners(corner_a, corner_b, corner_c, corner_d)
