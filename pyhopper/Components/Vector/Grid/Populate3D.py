"""Populate3D - Populate a 3-Dimensional region with points (Grasshopper "Populate 3D")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Utils.Sampling import populate_box


class Populate3D(Component):
    """Populate a 3-Dimensional region with points.

    Inputs:
        region: Box that defines the 3D region for point insertion (Grasshopper Region [item]).
        count: Number of points to add (Grasshopper Count [item]).
        seed: Random seed for insertion (Grasshopper Seed [item]).
        points: Optional pre-existing population (Grasshopper Points [list]).

    Outputs:
        population: Population of inserted points (Grasshopper Population).

    Notes:
        Grasshopper: Vector > Grid > Populate 3D (Pop3D).
        pyhopper decisions: Mitchell's best-candidate sampling inside the box (seed points repel but
        are not emitted), deterministic per seed but a different sequence from Grasshopper; defaults
        box 10×10×2 centred at (5, 5, 1), 100 points, seed 1.
    """

    display_name = "Populate 3D"
    nickname = "Pop3D"
    gh_guid = "e202025b-dc8e-4c51-ae19-4415b172886f"

    inputs = [
        InputParam("region", AtomicBox, Access.ITEM, default=AtomicBox(AtomicPlane.world_xy(AtomicPoint(5.0, 5.0, 1.0)), 10.0, 10.0, 2.0)),
        InputParam("count", int, Access.ITEM, default=100),
        InputParam("seed", int, Access.ITEM, default=1),
        InputParam("points", AtomicPoint, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("population", AtomicPoint, access=Access.LIST),
    ]

    def generate(self, region=None, count=100, seed=1, points=None):
        box = region if region is not None else AtomicBox(AtomicPlane.world_xy(AtomicPoint(5.0, 5.0, 1.0)), 10.0, 10.0, 2.0)
        return populate_box(box, int(count), int(seed), list(points or []))
