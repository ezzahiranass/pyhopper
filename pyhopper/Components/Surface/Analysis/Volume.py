"""Volume - Compute closed geometry volume and centroid."""

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.MassProperties import volume_properties


class Volume(Component):
    """Solve volume properties for closed Breps, meshes, and surfaces."""

    inputs = [InputParam("geometry", None, Access.ITEM)]
    outputs = [
        OutputParam("volume", float),
        OutputParam("centroid", AtomicPoint),
    ]

    def generate(self, geometry=None):
        return volume_properties(geometry)
