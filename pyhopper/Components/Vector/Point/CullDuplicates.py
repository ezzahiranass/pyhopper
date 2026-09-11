"""CullDuplicates - Cull points that are coincident within tolerance (Grasshopper "Cull Duplicates")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Points import average_point, group_coincident


class CullDuplicates(Component):
    """Cull points that are coincident within tolerance.

    Inputs:
        points: Points to operate on (Grasshopper Points [list]).
        tolerance: Proximity tolerance distance (Grasshopper Tolerance [item]).

    Outputs:
        points: Culled points (Grasshopper Points).
        indices: Index map of culled points (Grasshopper Indices).
        valence: Number of input points represented by this output point (Grasshopper Valence).

    Notes:
        Grasshopper: Vector > Point > Cull Duplicates (CullPt).
        pyhopper decisions: Grasshopper's default "Average" mode: points within ``tolerance`` of the first
        point of a group are replaced by the group's average; ``indices`` gives the original
        index of a lone point and ``-1`` for an averaged one; ``valence`` is the group size;
        Grasshopper default ``tolerance = 0.1``. The Leave One / Cull All menu modes are not exposed.
    """

    display_name = "Cull Duplicates"
    nickname = "CullPt"
    gh_guid = "6eaffbb2-3392-441a-8556-2dc126aa8910"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
        InputParam("tolerance", float, Access.ITEM, default=0.1),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("indices", int, access=Access.LIST),
        OutputParam("valence", int, access=Access.LIST),
    ]

    def generate(self, points=None, tolerance=0.1):
        source = list(points or [])
        groups = group_coincident(source, float(tolerance))
        culled = [average_point([source[index] for index in group]) for group in groups]
        indices = [group[0] if len(group) == 1 else -1 for group in groups]
        return culled, indices, [len(group) for group in groups]
