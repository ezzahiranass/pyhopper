"""Brep - Typed boundary-representation parameter container."""

from pyhopper.Core.Atoms import AtomicBrep
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Brep(Component):
    """Contain Breps, converting boxes and single surfaces exactly."""

    inputs = [InputParam("brep", AtomicBrep, Access.ITEM)]
    outputs = [OutputParam("brep", AtomicBrep)]

    def generate(self, brep=None):
        return brep
