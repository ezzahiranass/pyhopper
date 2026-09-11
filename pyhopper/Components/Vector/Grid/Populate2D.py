"""Populate2D - Populate a 2-Dimensional region with points (Grasshopper "Populate 2D")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicRectangle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Sampling import populate_rectangle


class Populate2D(Component):
    """Populate a 2-Dimensional region with points.

    Inputs:
        region: Rectangle that defines the 2D region for point insertion (Grasshopper Region [item]).
        count: Number of points to add (Grasshopper Count [item]).
        seed: Random seed for insertion (Grasshopper Seed [item]).
        points: Optional pre-existing population (Grasshopper Points [list]).

    Outputs:
        population: Population of inserted points (Grasshopper Population).

    Notes:
        Grasshopper: Vector > Grid > Populate 2D (Pop2D).
        pyhopper decisions: Mitchell best-candidate sampling inside the rectangle: every new point is the
        farthest of several random draws from the points placed so far; optional seed points
        repel but are not emitted. Deterministic per seed but a different sequence from
        Grasshopper's. Grasshopper defaults ``count = 100``, ``seed = 1``.
    """

    display_name = "Populate 2D"
    nickname = "Pop2D"
    gh_guid = "e2d958e8-9f08-44f7-bf47-a684882d0b2a"

    inputs = [
        InputParam("region", AtomicRectangle, Access.ITEM),
        InputParam("count", int, Access.ITEM, default=100),
        InputParam("seed", int, Access.ITEM, default=1),
        InputParam("points", AtomicPoint, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("population", AtomicPoint, access=Access.LIST),
    ]

    def generate(self, region=None, count=100, seed=1, points=None):
        if region is None:
            raise ValueError("Populate 2D needs a region rectangle")
        return populate_rectangle(region, int(count), int(seed), list(points or []))
