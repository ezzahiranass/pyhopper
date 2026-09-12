"""Planar - Test a curve for planarity (Grasshopper "Planar")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_planarity
from pyhopper.Core.TypeSystem import CURVE


class Planar(Component):
    """Test a curve for planarity.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).

    Outputs:
        planar: Planarity of curve (Grasshopper Planar).
        plane: Curve plane (Grasshopper Plane).
        deviation: Deviation from curve plane (Grasshopper Deviation).

    Notes:
        Grasshopper: Curve > Analysis > Planar (Planar).
        pyhopper decisions: arcs, circles and rectangles report their own plane, a line the plane
        through it with world-Z-ish normal, a planar polyline its first vertex / Newell normal / first
        edge (all Grasshopper-verified); a non-planar curve reports the least-squares plane of 256
        sampled points (normal towards +Z) and the largest distance as deviation — Grasshopper's own
        fit samples differently, so those numbers are close rather than identical. Planar means a
        deviation below 1e-6.
    """

    display_name = "Planar"
    nickname = "Planar"
    gh_guid = "5816ec9c-f170-4c59-ac44-364401ff84cd"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("planar", bool),
        OutputParam("plane", AtomicPlane),
        OutputParam("deviation", float),
    ]

    def generate(self, curve=None):
        plane, deviation = curve_planarity(curve)
        return deviation <= 1e-6, plane, deviation
