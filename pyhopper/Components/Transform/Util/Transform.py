"""Transform - Transform an object (Grasshopper "Transform")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Core.TypeSystem import GEOMETRY


class Transform(Component):
    """Transform an object.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        transform: Transformation (Grasshopper Transform [item]).

    Outputs:
        geometry: Transformed geometry (Grasshopper Geometry).

    Notes:
        Grasshopper: Transform > Util > Transform (Transform).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Transform"
    nickname = "Transform"
    gh_guid = "610e689b-5adc-47b3-af8f-e3a32b7ea341"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM),
        InputParam("transform", AtomicTransform, Access.ITEM),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
    ]

    def generate(self, geometry=None, transform=None):
        return apply_transform(transform, geometry)
