"""Surface - Typed surface parameter container."""

from pyhopper.Core.Atoms import AtomicSurface
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Surface(Component):
    """Contain surfaces and unwrap unambiguous single-face Breps."""

    inputs = [InputParam("surface", AtomicSurface, Access.ITEM)]
    outputs = [OutputParam("surface", AtomicSurface)]

    def generate(self, surface=None):
        return surface
