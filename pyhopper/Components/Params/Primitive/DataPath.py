"""DataPath - Contains a collection of data paths (Grasshopper "Data Path")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Path import Path


class DataPath(Component):
    """Contains a collection of data paths.

    Inputs:
        path: Paths to contain (Grasshopper Data Path); text such as ``{0;1}`` and integers coerce.

    Outputs:
        path: The same paths (Grasshopper Data Path).

    Notes:
        Grasshopper: Params > Primitive > Data Path (Path).
        pyhopper decisions: a container like ``Domain``; paths flow as ``Path`` items, print as
        ``{0;1}`` and coerce from text or integers (the K7 unlock of the component roadmap).
    """

    display_name = "Data Path"
    nickname = "Path"
    gh_guid = "56c9c942-791f-4eeb-a4f0-82b93f1c0909"

    inputs = [InputParam("path", Path, Access.ITEM)]
    outputs = [OutputParam("path", Path)]

    def generate(self, path=None):
        return path
