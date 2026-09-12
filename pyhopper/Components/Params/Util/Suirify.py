"""Suirify - Suire-style simplification of data trees (Grasshopper "Suirify")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class Suirify(Component):
    """Suire-style simplification of data trees.

    Notes:
        Grasshopper: Params > Util > Suirify (Suirify).
        pyhopper decisions: a parameter container like ``Data``: one ``data`` input and output with
        whole-tree access; Grasshopper 8 (headless, fed from a Data container) simplifies the paths
        the way Simplify Tree does — shared leading indices are removed and a single branch keeps
        its path — without flattening single-item branches, so that is what pyhopper does.
    """

    display_name = "Suirify"
    nickname = "Suirify"
    gh_guid = "5d4e1eeb-482e-42a7-aa2f-e5deb8a1018e"

    inputs = [InputParam("data", None, Access.TREE, default=[])]
    outputs = [OutputParam("data", access=Access.TREE)]

    def generate(self, data=None):
        return (DataTree() if data is None else data).simplify()
