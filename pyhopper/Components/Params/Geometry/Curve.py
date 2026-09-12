"""Curve - Validate and pass through curve geometry."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE


class Curve(Component):
    """Contain supported curve atoms while preserving named authoring types."""

    inputs = [InputParam("curve", CURVE, Access.ITEM)]
    outputs = [OutputParam("curve", CURVE)]

    def generate(self, curve=None):
        return curve
