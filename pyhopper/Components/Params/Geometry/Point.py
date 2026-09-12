"""Point - Validate and pass through point geometry."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Point(Component):
    """Contain and normalize a DataTree of point values."""

    inputs = [InputParam("point", AtomicPoint, Access.ITEM)]
    outputs = [OutputParam("point", AtomicPoint)]

    def generate(self, point=None):
        return point
