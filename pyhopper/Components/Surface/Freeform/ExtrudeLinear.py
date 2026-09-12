"""ExtrudeLinear - Extrude curves and surfaces along a straight path (Grasshopper "Extrude Linear")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBrep, AtomicLine, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicBrep, AtomicLine, AtomicPoint, AtomicPolyline, AtomicRectangle, AtomicSurface, AtomicTransform
from pyhopper.Utils.SurfaceBuilders import extrude_along, rectangle_corners
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Planes import plane_from_normal
from pyhopper.Utils.Vectors import is_zero, vector_between
from pyhopper.Core.TypeSystem import GEOMETRY


class ExtrudeLinear(Component):
    """Extrude curves and surfaces along a straight path.

    Inputs:
        profile: Profile curve or surface (Grasshopper Profile [item]).
        profile_orientation: Plane indicating orientation of profile shape (Grasshopper Orientation (P) [item]).
        axis: Extrusion axis (Grasshopper Axis [item]).
        axis_orientation: Optional orientational plane for the axis (Grasshopper Orientation (A) [item]).

    Outputs:
        extrusion: Extrusion result (Grasshopper Extrusion).

    Notes:
        Grasshopper: Surface > Freeform > Extrude Linear (Extrude).
        pyhopper decisions: the profile is moved from its orientation plane (world XY by default) onto
        the axis orientation plane — by default the plane at the axis start whose normal is the axis, so
        a profile drawn at the origin lands on the axis (Grasshopper-verified) — and swept along the
        axis vector. Like Grasshopper, curves give one surface (U along the extrusion over
        ``[0, |axis|]``, V the profile), polylines and rectangles one face per edge as a Brep, and
        nothing is capped; points and surfaces raise ``ValueError``.
    """

    display_name = "Extrude Linear"
    nickname = "Extrude"
    gh_guid = "8efd5eb9-a896-486e-9f98-d8d1a07a49f3"

    inputs = [
        InputParam("profile", GEOMETRY, Access.ITEM),
        InputParam("profile_orientation", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("axis", AtomicLine, Access.ITEM),
        InputParam("axis_orientation", AtomicPlane, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("extrusion", GEOMETRY),
    ]

    def generate(self, profile=None, profile_orientation=AtomicPlane.world_xy(), axis=None, axis_orientation=None):
        direction = vector_between(axis.start, axis.end)
        if is_zero(direction):
            raise ValueError("ExtrudeLinear needs an axis with a direction")
        target = axis_orientation if axis_orientation is not None else plane_from_normal(axis.start, direction)
        source = profile_orientation if profile_orientation is not None else AtomicPlane.world_xy()
        profile = apply_transform(AtomicTransform.plane_to_plane(source, target), profile)
        if isinstance(profile, AtomicPoint):
            raise ValueError("ExtrudeLinear cannot extrude a point")
        if isinstance(profile, (AtomicPolyline, AtomicRectangle)):
            vertices = list(profile.points) if isinstance(profile, AtomicPolyline) else rectangle_corners(profile)
            faces = [extrude_along(as_nurbs_curve(AtomicLine(start, end)), direction) for start, end in zip(vertices, vertices[1:])]
            return AtomicBrep(tuple(faces))
        if isinstance(profile, AtomicSurface):
            raise ValueError("ExtrudeLinear extrudes curves; use Extrude for surfaces")
        return extrude_along(as_nurbs_curve(profile), direction)
