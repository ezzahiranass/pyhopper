"""CameraObscura - Camera Obscura (point mirror) transformation (Grasshopper "Camera Obscura")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Core.TypeSystem import GEOMETRY


class CameraObscura(Component):
    """Camera Obscura (point mirror) transformation.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        point: Mirror point (Grasshopper Point [item]).
        factor: Scaling factor (Grasshopper Factor [item]).

    Outputs:
        geometry: Mirrored geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Affine > Camera Obscura (CO).
        pyhopper decisions: Grasshopper-verified — the point reflection through ``point`` scaled by
        ``factor``: ``x' = point - factor · (x - point)`` (an affine map, no perspective); without
        geometry only the transform is emitted. Default factor 1.
    """

    display_name = "Camera Obscura"
    nickname = "CO"
    gh_guid = "407e35c6-7c40-4652-bd80-fde1eb7ec034"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM, optional=True),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, point=AtomicPoint.origin(), factor=1.0):
        f = float(factor)
        xform = AtomicTransform._from_linear(((-f, 0.0, 0.0), (0.0, -f, 0.0), (0.0, 0.0, -f)), ((1.0 + f) * point.x, (1.0 + f) * point.y, (1.0 + f) * point.z))
        return (Component.NO_OUTPUT if geometry is None else apply_transform(xform, geometry)), xform
