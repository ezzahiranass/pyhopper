"""RotateDirection - Rotate an object from one direction to another (Grasshopper "Rotate Direction")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicTransform, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Core.TypeSystem import GEOMETRY


class RotateDirection(Component):
    """Rotate an object from one direction to another.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        center: Rotation center point (Grasshopper Center [item]).
        from_vector: Initial direction (Grasshopper From [item]).
        to: Final direction (Grasshopper To [item]).

    Outputs:
        geometry: Rotated geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Euclidean > Rotate Direction (Rotate).
        pyhopper decisions: the minimal rotation about ``center`` taking ``from`` onto ``to`` (opposite
        vectors turn half a circle about Rhino's perpendicular axis, matching Grasshopper); without
        geometry only the transform is emitted. Defaults X to Y as in Grasshopper.
    """

    display_name = "Rotate Direction"
    nickname = "Rotate"
    gh_guid = "5edaea74-32cb-4586-bd72-66694eb73160"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM, optional=True),
        InputParam("center", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("from_vector", AtomicVector, Access.ITEM, default=AtomicVector.unit_x()),
        InputParam("to", AtomicVector, Access.ITEM, default=AtomicVector.unit_y()),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, center=AtomicPoint.origin(), from_vector=AtomicVector.unit_x(), to=AtomicVector.unit_y()):
        xform = AtomicTransform.rotation_to_direction(center, from_vector, to)
        return (Component.NO_OUTPUT if geometry is None else apply_transform(xform, geometry)), xform
