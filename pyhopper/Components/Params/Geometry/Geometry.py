"""Geometry - Validate and pass through any geometry atom."""

from __future__ import annotations

from pyhopper.Core.Atoms import (
    Atom,
    AtomicArc,
    AtomicBrep,
    AtomicCircle,
    AtomicCylinder,
    AtomicLine,
    AtomicMesh,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicSurface,
)
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


GEOMETRY_TYPES = (
    AtomicPoint,
    AtomicLine,
    AtomicCircle,
    AtomicArc,
    AtomicPolyline,
    AtomicNurbsCurve,
    AtomicSurface,
    AtomicMesh,
    AtomicBrep,
    AtomicCylinder,
    AtomicPlane,
)


class Geometry(Component):
    """Validate and pass through any geometry atom unchanged.

    This parameter-style component acts as a universal typed container. It
    accepts any supported geometry atom and returns it unchanged while the
    inherited pipeline preserves the surrounding ``DataTree`` structure.
    """

    inputs = [InputParam("geometry", None, Access.ITEM)]
    outputs = [OutputParam("geometry")]

    def generate(self, geometry=None):
        """Return the incoming geometry after type validation."""
        if not isinstance(geometry, GEOMETRY_TYPES):
            raise TypeError(
                f"Geometry expected a geometry atom, got {type(geometry).__name__}"
            )
        return geometry
