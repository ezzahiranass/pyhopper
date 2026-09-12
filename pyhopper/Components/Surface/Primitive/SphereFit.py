"""SphereFit - Fit a sphere to a 3D collection of points (Grasshopper "Sphere Fit")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Fitting import fit_sphere

from .Sphere import Sphere
from pyhopper.Core.TypeSystem import SURFACE


class SphereFit(Component):
    """Fit a sphere to a 3D collection of points.

    Inputs:
        points: Points to fit (Grasshopper Points [list]).

    Outputs:
        center: Center of fitted sphere (Grasshopper Center).
        radius: Radius of fitted sphere (Grasshopper Radius).
        sphere: Sphere surface (Grasshopper Sphere).

    Notes:
        Grasshopper: Surface > Primitive > Sphere Fit (SFit).
        pyhopper decisions: an algebraic least-squares sphere refined by Gauss-Newton on the radial
        residuals, which reproduces Rhino's fit (Grasshopper-verified on exact and noisy clouds);
        fewer than four points or coplanar points give the sphere on their fitted circle, as in
        Grasshopper. The surface is the same 9x5 rational pole grid as the Sphere component.
    """

    display_name = "Sphere Fit"
    nickname = "SFit"
    gh_guid = "e7ffb3af-2d77-4804-a260-755308bf8285"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
    ]
    outputs = [
        OutputParam("center", AtomicPoint),
        OutputParam("radius", float),
        OutputParam("sphere", SURFACE),
    ]

    def generate(self, points=None):
        centre, radius = fit_sphere(list(points or []))
        return centre, radius, Sphere(AtomicPlane.world_xy(centre), radius).all_items()[0]
