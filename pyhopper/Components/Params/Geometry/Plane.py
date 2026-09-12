"""Plane - Typed plane parameter container."""

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Plane(Component):
    """Contain planes, converting incoming points to World-XY planes."""

    inputs = [InputParam("plane", AtomicPlane, Access.ITEM)]
    outputs = [OutputParam("plane", AtomicPlane)]

    def generate(self, plane=None):
        return plane
