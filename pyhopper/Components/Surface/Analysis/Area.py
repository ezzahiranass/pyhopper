"""Area - Compute geometry area and area centroid."""

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.MassProperties import area_properties


class Area(Component):
    """Solve area properties for Breps, meshes, surfaces, and planar closed curves."""

    inputs = [InputParam("geometry", None, Access.ITEM)]
    outputs = [
        OutputParam("area", float),
        OutputParam("centroid", AtomicPoint),
    ]

    def generate(self, geometry=None):
        return area_properties(geometry)
