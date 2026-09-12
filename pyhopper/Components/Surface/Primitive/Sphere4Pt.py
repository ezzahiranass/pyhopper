"""Sphere4Pt - Create a spherical surface from 4 points (Grasshopper "Sphere 4Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Components.Surface.Primitive.Sphere import Sphere
from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Utils.CurveFitting import fit_circle
from pyhopper.Utils.Hull import sphere_through_points
from pyhopper.Core.TypeSystem import SURFACE


class Sphere4Pt(Component):
    """Create a spherical surface from 4 points.

    Inputs:
        point_1: First point (Grasshopper Point 1 [item]).
        point_2: Second point (cannot be coincident with P1) (Grasshopper Point 2 [item]).
        point_3: Third point (cannot be colinear with P1 & P2) (Grasshopper Point 3 [item]).
        point_4: Fourth point (cannot be coplanar with P1, P2 & P3) (Grasshopper Point 4 [item]).

    Outputs:
        center: Center of sphere (Grasshopper Center).
        radius: Radius of sphere (Grasshopper Radius).
        sphere: Sphere fitted to P1~P4 (Grasshopper Sphere).

    Notes:
        Grasshopper: Surface > Primitive > Sphere 4Pt (Sph4Pt).
        pyhopper decisions: the sphere through the four points; when they are coplanar Grasshopper
        falls back to the sphere on their common circle, and so does pyhopper (collinear points
        raise ``ValueError``). The surface is the same 9x5 rational pole grid as the Sphere component.
    """

    display_name = "Sphere 4Pt"
    nickname = "Sph4Pt"
    gh_guid = "b083c06d-9a71-4f40-b354-1d80bba1e858"

    inputs = [
        InputParam("point_1", AtomicPoint, Access.ITEM),
        InputParam("point_2", AtomicPoint, Access.ITEM),
        InputParam("point_3", AtomicPoint, Access.ITEM),
        InputParam("point_4", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("center", AtomicPoint),
        OutputParam("radius", float),
        OutputParam("sphere", SURFACE),
    ]

    def generate(self, point_1=None, point_2=None, point_3=None, point_4=None):
        solved = sphere_through_points(point_1, point_2, point_3, point_4)
        if solved is None:
            circle, _ = fit_circle([point_1, point_2, point_3, point_4])
            centre, radius = circle.plane.origin, float(circle.radius)
        else:
            centre, radius = solved
        if radius <= 1e-12:
            raise ValueError("Sphere4Pt needs four distinct points")
        return centre, radius, Sphere(AtomicPlane.world_xy(centre), radius).all_items()[0]
