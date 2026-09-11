"""Entwine - Flatten and combine a collection of data streams (Grasshopper "Entwine")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class Entwine(Component):
    """Flatten and combine a collection of data streams.

    Inputs:
        branches: Data to entwine (Grasshopper Branch {0;0} / Branch {0;1} / Branch {0;2} [tree]).

    Outputs:
        result: Entwined result (Grasshopper Result).

    Notes:
        Grasshopper: Sets > Tree > Entwine (Entwine).
        pyhopper decisions: each stream is flattened into its own branch ``{0;i}`` (Grasshopper's default
        "Flatten Inputs" behaviour); pyhopper emits one branch per connected stream where
        Grasshopper also emits an empty branch for each unconnected port.
    """

    display_name = "Entwine"
    nickname = "Entwine"
    gh_guid = "c9785b8e-2f30-4f90-8ee3-cca710f82402"

    inputs = [
        InputParam("branches", None, Access.TREE, optional=True),
    ]
    outputs = [
        OutputParam("result"),
    ]
    variadic_inputs = True

    def generate(self, branches=()):
        return DataTree.entwine(*(branches or ()))
