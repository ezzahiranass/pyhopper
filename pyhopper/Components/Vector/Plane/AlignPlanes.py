"""AlignPlanes - Align planes by minimizing their serial rotation (Grasshopper "Align Planes")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._alignment import align_to


class AlignPlanes(Component):
    """Align planes by minimizing their serial rotation.

    Inputs:
        planes: Planes to align (Grasshopper Planes [list]).
        master: Optional master plane (if omitted the first plane in P is the master plane). (Grasshopper Master [item]).

    Outputs:
        planes: Aligned planes (Grasshopper Planes).

    Notes:
        Grasshopper: Vector > Plane > Align Planes (Align).
        pyhopper decisions: Grasshopper-verified — each plane is rotated about its normal so that its
        x axis follows the previous (already aligned) plane's x axis projected onto it; when that
        projection vanishes the y axes are matched instead; the first plane follows ``master`` or
        stays as it is.
    """

    display_name = "Align Planes"
    nickname = "Align"
    gh_guid = "2318aee8-01fe-4ea8-9524-6966023fc622"

    inputs = [
        InputParam("planes", AtomicPlane, Access.LIST),
        InputParam("master", AtomicPlane, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("planes", AtomicPlane, access=Access.LIST),
    ]

    def generate(self, planes=None, master=None):
        aligned = []
        reference = master
        for plane in (planes or []):
            if reference is not None:
                plane = align_to(plane, reference)
            aligned.append(plane)
            reference = plane
        return aligned
