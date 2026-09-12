"""PlaneFit - Fit a plane through a set of points (Grasshopper "Plane Fit")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Fitting import fit_plane


class PlaneFit(Component):
    """Fit a plane through a set of points.

    Inputs:
        points: Points to fit (Grasshopper Points [list]).

    Outputs:
        plane: Plane definition (Grasshopper Plane).
        deviation: Maximum deviation between points and plane (Grasshopper Deviation).

    Notes:
        Grasshopper: Vector > Plane > Plane Fit (PlFit).
        pyhopper decisions: least-squares plane by a Jacobi eigen-solve of the covariance; like
        Grasshopper the origin is the world origin projected onto the plane, the x axis follows
        Rhino's ``PerpendicularTo`` rule and ``deviation`` is the largest point distance. The
        normal is oriented towards +Z (then +Y, then +X) — Grasshopper's sign is whatever its
        solver returns. Fewer than three or collinear points raise ``ValueError``.
    """

    display_name = "Plane Fit"
    nickname = "PlFit"
    gh_guid = "33bfc73c-19b2-480b-81e6-f3523a012ea6"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
        OutputParam("deviation", float),
    ]

    def generate(self, points=None):
        return fit_plane(list(points or []))
