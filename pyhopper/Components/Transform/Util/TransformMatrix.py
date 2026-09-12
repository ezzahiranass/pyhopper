"""TransformMatrix - A 4x4 Transformation matrix (Grasshopper "Transform Matrix")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class TransformMatrix(Component):
    """A 4x4 Transformation matrix.

    Inputs:
        transform: Transform atoms to contain (Grasshopper Transform Matrix).

    Outputs:
        transform: The same transforms (Grasshopper Transform Matrix).

    Notes:
        Grasshopper: Transform > Util > Transform Matrix (Matrix).
        pyhopper decisions: the Grasshopper parameter for 4x4 matrices; a container with one input and one output of the same
        name like ``Params > Geometry > Transform``, so Grasshopper definitions keep resolving by GUID.
    """

    display_name = "Transform Matrix"
    nickname = "Matrix"
    gh_guid = "93c24899-f456-4785-84f2-314958b9347b"

    inputs = [InputParam("transform", AtomicTransform, Access.ITEM)]
    outputs = [OutputParam("transform", AtomicTransform)]

    def generate(self, transform=None):
        return transform
