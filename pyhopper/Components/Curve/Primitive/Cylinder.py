"""Cylinder - Create a cylinder from radius and height."""

from pyhopper.Core.Atoms import AtomicCylinder, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Cylinder(Component):
    """Create an ``AtomicCylinder`` atom from a radius and height."""

    inputs = [
        InputParam("radius", float, Access.ITEM, default=1.0),
        InputParam("height", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("cylinder")]

    def generate(self, radius=1.0, height=1.0):
        return AtomicCylinder(
            plane=AtomicPlane.world_xy(),
            radius=float(radius),
            height=float(height),
        )
