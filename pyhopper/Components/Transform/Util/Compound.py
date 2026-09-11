"""Compound - Compound two transformations (Grasshopper "Compound")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Compound(Component):
    """Compound two transformations.

    Inputs:
        transforms: Transformations to compound (Grasshopper Transforms [list]).

    Outputs:
        compound: Compound transformation (Grasshopper Compound).

    Notes:
        Grasshopper: Transform > Util > Compound (Comp).
        pyhopper decisions: transforms compose in list order (the first is applied first), like Grasshopper; an empty
        list gives the identity.
    """

    display_name = "Compound"
    nickname = "Comp"
    gh_guid = "ca80054a-cde0-4f69-a132-10502b24866d"

    inputs = [
        InputParam("transforms", AtomicTransform, Access.LIST),
    ]
    outputs = [
        OutputParam("compound", AtomicTransform),
    ]

    def generate(self, transforms=None):
        return AtomicTransform.compound(list(transforms or []))
