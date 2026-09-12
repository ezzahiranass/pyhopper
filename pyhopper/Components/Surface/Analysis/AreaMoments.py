"""AreaMoments - Solve area moments for breps, meshes and planar closed curves (Grasshopper "Area Moments")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.MassProperties import area_moments
from pyhopper.Core.TypeSystem import GEOMETRY


class AreaMoments(Component):
    """Solve area moments for breps, meshes and planar closed curves.

    Inputs:
        geometry: Brep, mesh or planar closed curve for area computation (Grasshopper Geometry [item]).

    Outputs:
        area: Area of geometry (Grasshopper Area).
        centroid: Volume centroid of geometry (Grasshopper Centroid).
        inertia: Moments of inertia around the centroid (Grasshopper Inertia).
        secondary: Secondary moments of inertia around the centroid (Grasshopper Secondary).
        gyration: Radii of gyration (Grasshopper Gyration).

    Notes:
        Grasshopper: Surface > Analysis > Area Moments (AMoments).
        pyhopper decisions: Grasshopper-verified — area, area centroid and, about the centroid in world
        axes, the moments of inertia (∫y²+z², ∫x²+z², ∫x²+y²), the second moments (∫x², ∫y², ∫z²) and
        the radii of gyration. Planar closed curves are integrated exactly (polylines, rectangles,
        circles, ellipses) or from dense samples, surfaces and breps by Gauss-Legendre quadrature per
        knot span, meshes and boxes by their facets.
    """

    display_name = "Area Moments"
    nickname = "AMoments"
    gh_guid = "1eb7b856-ec7d-40b6-a76c-f216a11df37c"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM),
    ]
    outputs = [
        OutputParam("area", float),
        OutputParam("centroid", AtomicPoint),
        OutputParam("inertia", AtomicVector),
        OutputParam("secondary", AtomicVector),
        OutputParam("gyration", AtomicVector),
    ]

    def generate(self, geometry=None):
        return area_moments(geometry)
