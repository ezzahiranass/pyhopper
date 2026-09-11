"""InverseTransform - Invert a transformation (Grasshopper "Inverse Transform")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class InverseTransform(Component):
    """Invert a transformation.

    Inputs:
        transform: Transformation to inverse (Grasshopper Transform [item]).

    Outputs:
        transform: Inversed transformation (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Util > Inverse Transform (Inverse).
        pyhopper decisions: a singular transform raises ``ValueError`` (Grasshopper reports an error).
    """

    display_name = "Inverse Transform"
    nickname = "Inverse"
    gh_guid = "51f61166-7202-45aa-9126-3d83055b269e"

    inputs = [
        InputParam("transform", AtomicTransform, Access.ITEM),
    ]
    outputs = [
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, transform=None):
        return transform.inverse()
