"""Project - Project an object onto a plane (Grasshopper "Project")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform


class Project(Component):
    """Project an object onto a plane.

    Inputs:
        geometry: Geometry to project (Grasshopper Geometry [item]).
        plane: Projection plane (Grasshopper Plane [item]).

    Outputs:
        geometry: Projected geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Affine > Project (Project).
        pyhopper decisions: orthogonal projection onto the plane (``AtomicTransform.projection``); without geometry
        only the transform is emitted. Circles and arcs collapse to NURBS when the projection is
        singular for them.
    """

    display_name = "Project"
    nickname = "Project"
    gh_guid = "23285717-156c-468f-a691-b242488c06a6"

    inputs = [
        InputParam("geometry", None, Access.ITEM, optional=True),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, plane=AtomicPlane.world_xy()):
        xform = AtomicTransform.projection(plane)
        return (Component.NO_OUTPUT if geometry is None else apply_transform(xform, geometry)), xform
