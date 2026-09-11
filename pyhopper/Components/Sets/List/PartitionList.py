"""PartitionList - Partition each list branch into fixed-size chunks."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class PartitionList(Component):
    """Partition every incoming branch into fixed-size sub-branches.

    Chunk ``k`` of the branch at ``{path}`` is written to ``{path;k}``. The
    ``size`` list is cycled with its last value repeated (Grasshopper rule), so
    ``[1, 2]`` yields chunks of 1, 2, 2, 2, … Sizes below one are clamped to one.
    An empty branch produces a single empty chunk at ``{path;0}``.
    """

    display_name = "Partition List"
    nickname = "Partition"
    gh_guid = "5a93246d-2595-4c28-bc2d-90657634f92a"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("size", int, Access.LIST, default=2),
    ]
    outputs = [OutputParam("chunks", access=Access.TREE)]

    def generate(self, list=None, size=2):
        """Return the chunks of the incoming branch as sub-branches."""
        branch = list if isinstance(list, (tuple, builtins.list)) else [list]
        sizes = [max(1, int(value)) for value in (size if isinstance(size, builtins.list) else [size])] or [2]

        chunks: list[list] = []
        position = 0
        while position < len(branch):
            chunk_size = sizes[min(len(chunks), len(sizes) - 1)]
            chunks.append(branch[position : position + chunk_size])
            position += chunk_size
        return self.sub_branches(chunks or [[]])
