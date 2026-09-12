"""Split - Split a compound transformation into fragments (Grasshopper "Split")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Split(Component):
    """Split a compound transformation into fragments.

    Inputs:
        transform: Compound transformation (Grasshopper Transform [item]).

    Outputs:
        fragments: Fragments making up the compound transformation (Grasshopper Fragments).

    Notes:
        Grasshopper: Transform > Util > Split (Split).
        pyhopper decisions: Grasshopper splits a compound transform into the fragments it was built
        from; pyhopper transforms are plain matrices with no history, so — like Grasshopper for a
        plain matrix — the transform itself is the only fragment.
    """

    display_name = "Split"
    nickname = "Split"
    gh_guid = "915f8f93-f5d1-4a7b-aecb-c327bab88ffb"

    inputs = [
        InputParam("transform", AtomicTransform, Access.ITEM),
    ]
    outputs = [
        OutputParam("fragments", AtomicTransform, access=Access.LIST),
    ]

    def generate(self, transform=None):
        return [transform]
