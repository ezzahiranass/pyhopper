"""SubList - Extract an inclusive domain of items from each list branch."""

from __future__ import annotations

import builtins

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _domain_indices(domain: AtomicInterval) -> range:
    start = int(domain.start)
    end = int(domain.end)
    step = 1 if end >= start else -1
    return range(start, end + step, step)


class SubList(Component):
    """Extract an inclusive index domain from each incoming branch.

    ``list`` is a whole-branch (LIST) input; ``domain`` and ``wrap`` are ITEM
    inputs. With ``wrap`` enabled, out-of-range indices wrap into the branch.
    The second output contains the resolved branch-local indices.
    """

    display_name = "Sub List"
    nickname = "SubSet"
    gh_guid = "b333ff42-93bd-406b-8e17-15780719b6ec"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("domain", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
        InputParam("wrap", bool, Access.ITEM, default=False),
    ]
    outputs = [OutputParam("list"), OutputParam("index", int)]

    def generate(self, list=None, domain=AtomicInterval(0.0, 1.0), wrap=False):
        """Return the selected items and their resolved indices."""
        branch = list if isinstance(list, (tuple, builtins.list)) else [list]
        if not branch:
            return [], []

        requested_indices = _domain_indices(domain)
        if wrap:
            resolved_indices = [index % len(branch) for index in requested_indices]
        else:
            resolved_indices = [index for index in requested_indices if 0 <= index < len(branch)]

        return [branch[index] for index in resolved_indices], resolved_indices
