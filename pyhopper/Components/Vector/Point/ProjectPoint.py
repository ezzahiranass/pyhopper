"""ProjectPoint - Project a point onto a collection of shapes (Grasshopper "Project Point")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import geometry_ray_hit
from pyhopper.Core.TypeSystem import GEOMETRY


class ProjectPoint(Component):
    """Project a point onto a collection of shapes.

    Inputs:
        point: Point to project (Grasshopper Point [item]).
        direction: Projection direction (Grasshopper Direction [item]).
        geometry: Geometry to project onto (Grasshopper Geometry [list]).

    Outputs:
        point: Projected point (Grasshopper Point).
        index: Index of object that was projected onto (Grasshopper Index).

    Notes:
        Grasshopper: Vector > Point > Project Point (Project).
        pyhopper decisions: Grasshopper-verified — a ray from the point along the direction (default
        (0, 0, -1)); surfaces, breps and boxes are hit exactly, curves and points count as hit where the
        ray passes within tolerance (the point on the ray is returned, as Grasshopper does), planes are
        intersected. The nearest hit along the ray wins (its list index); nothing behind the point
        counts. A miss emits no point and index -1. coincidence uses pyhopper's absolute tolerance (0.01, Rhino's default document tolerance that Grasshopper uses).
    """

    display_name = "Project Point"
    nickname = "Project"
    gh_guid = "5184b8cb-b71e-4def-a590-cd2c9bc58906"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("direction", AtomicVector, Access.ITEM, default=AtomicVector(0.0, 0.0, -1.0)),
        InputParam("geometry", GEOMETRY, Access.LIST),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("index", int),
    ]

    def generate(self, point=AtomicPoint.origin(), direction=AtomicVector(0.0, 0.0, -1.0), geometry=None):
        best = None
        for index, item in enumerate(geometry or []):
            hit = geometry_ray_hit(item, point, direction)
            if hit is not None and (best is None or hit[0] < best[0]):
                best = (hit[0], hit[1], index)
        if best is None:
            return Component.NO_OUTPUT, -1
        return best[1], best[2]
