"""Mesh - Contains a collection of polygon meshes (Grasshopper "Mesh")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicMesh
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Mesh(Component):
    """Contains a collection of polygon meshes.

    Inputs:
        mesh: Mesh atoms to contain (Grasshopper Mesh).

    Outputs:
        mesh: The same meshes (Grasshopper Mesh).

    Notes:
        Grasshopper: Params > Geometry > Mesh (Mesh).
        pyhopper decisions: a container like ``Arc``; meshes are ``AtomicMesh`` atoms (vertices and faces) — mesh construction
        and analysis components arrive with the K8 meshing kernel.
    """

    display_name = "Mesh"
    nickname = "Mesh"
    gh_guid = "1e936df3-0eea-4246-8549-514cb8862b7a"

    inputs = [InputParam("mesh", AtomicMesh, Access.ITEM)]
    outputs = [OutputParam("mesh", AtomicMesh)]

    def generate(self, mesh=None):
        return mesh
