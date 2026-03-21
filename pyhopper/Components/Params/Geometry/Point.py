"""Point - Validate and pass through point geometry."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Point(Component):
    """Validate and pass through ``AtomicPoint`` items unchanged.

    This is a typed parameter node equivalent: it checks that each incoming item
    is an ``AtomicPoint`` and then returns it unchanged while the inherited
    component pipeline preserves the surrounding ``DataTree`` structure.
    """

    inputs = [InputParam("point", AtomicPoint, Access.ITEM)]
    outputs = [OutputParam("point", AtomicPoint)]

    def generate(self, point=None):
        """Return the incoming point after type validation."""
        if not isinstance(point, AtomicPoint):
            raise TypeError(f"Point expected an AtomicPoint, got {type(point).__name__}")
        return point
