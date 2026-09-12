"""ConvexHull - Compute the planar, convex hull for a collection of points (Grasshopper "Convex Hull")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicPolyline
from pyhopper.Utils.Hull import convex_hull_indices
from pyhopper.Utils.Planes import project_point
from pyhopper.Core.TypeSystem import CURVE


class ConvexHull(Component):
    """Compute the planar, convex hull for a collection of points.

    Inputs:
        points: Points for convex hull solution (Grasshopper Points [list]).
        plane: Optional base plane. If no plane is provided, then the best-fit plane will be used. (Grasshopper Plane [item]).

    Outputs:
        hull: Convex hull in base plane space (Grasshopper Hull).
        hull_z: Convex hull in world space (Grasshopper Hull(z)).
        indices: Indices of points on convex hull (Grasshopper Indices).

    Notes:
        Grasshopper: Mesh > Triangulation > Convex Hull (Hull2D).
        pyhopper decisions: the hull of the points projected onto the plane (world XY by default),
        starting at the hull point with the largest plane x and running counter-clockwise, collinear
        edge points dropped — Grasshopper-verified; ``hull`` lies on the plane, ``hull_z`` uses the
        original points and ``indices`` lists the hull points. Fewer than three distinct points raise.
    """

    display_name = "Convex Hull"
    nickname = "Hull2D"
    gh_guid = "9d0c5284-ea24-4f9f-a183-ef57fc48b5b8"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("hull", CURVE),
        OutputParam("hull_z", CURVE),
        OutputParam("indices", int, access=Access.LIST),
    ]

    def generate(self, points=None, plane=AtomicPlane.world_xy()):
        cloud = list(points or [])
        indices = convex_hull_indices(cloud, plane)
        if len(indices) < 3:
            raise ValueError("ConvexHull needs at least three points that are not collinear")
        flat = [project_point(plane, cloud[index]) for index in indices]
        lifted = [cloud[index] for index in indices]
        return AtomicPolyline(tuple(flat + [flat[0]])), AtomicPolyline(tuple(lifted + [lifted[0]])), indices
