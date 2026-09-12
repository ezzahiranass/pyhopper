"""FitLine - Fit a line to a collection of points (Grasshopper "Fit Line")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveFitting import fit_line


class FitLine(Component):
    """Fit a line to a collection of points.

    Inputs:
        points: Points to fit (Grasshopper Points [list]).

    Outputs:
        line: Line segment (Grasshopper Line).

    Notes:
        Grasshopper: Curve > Primitive > Fit Line (FLine).
        pyhopper decisions: least-squares (principal axis) line spanning the extreme projections of the
        points, its direction oriented so its largest component is positive — Grasshopper-verified on
        ordered and shuffled input; fewer than two distinct points raise ``ValueError``.
    """

    display_name = "Fit Line"
    nickname = "FLine"
    gh_guid = "1f798a28-9de6-47b5-8201-cac57256b777"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
    ]
    outputs = [
        OutputParam("line", AtomicLine),
    ]

    def generate(self, points=None):
        return fit_line(list(points or []))
