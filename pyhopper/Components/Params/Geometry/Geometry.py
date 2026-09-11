"""Geometry - Validate and pass through any geometry atom."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import GEOMETRY


class Geometry(Component):
    """Contain any supported geometry atom without discarding authoring intent."""

    inputs = [InputParam("geometry", GEOMETRY, Access.ITEM)]
    outputs = [OutputParam("geometry", GEOMETRY)]

    def generate(self, geometry=None):
        return geometry
