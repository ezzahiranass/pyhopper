"""Curve - Validate and pass through curve geometry."""

from __future__ import annotations

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPolyline,
)
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


CURVE_TYPES = (
    AtomicLine,
    AtomicCircle,
    AtomicArc,
    AtomicPolyline,
    AtomicNurbsCurve,
)


class Curve(Component):
    """Validate and pass through curve atoms unchanged.

    This parameter-style component behaves as a typed container node. It accepts
    one item at a time, verifies that each item is one of pyhopper's supported
    curve atom types, and returns the same item unchanged so the surrounding
    ``DataTree`` structure is preserved by the inherited solve pipeline.
    """

    inputs = [InputParam("curve", None, Access.ITEM)]
    outputs = [OutputParam("curve")]

    def generate(self, curve=None):
        """Return the incoming curve after type validation."""
        if not isinstance(curve, CURVE_TYPES):
            raise TypeError(f"Curve expected a curve atom, got {type(curve).__name__}")
        return curve
