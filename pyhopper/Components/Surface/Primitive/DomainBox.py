"""DomainBox - Create a box defined by a base plane and size domains (Grasshopper "Domain Box")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicInterval, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import point_on_plane


class DomainBox(Component):
    """Create a box defined by a base plane and size domains.

    Inputs:
        base: Base plane (Grasshopper Base [item]).
        x: Domain of the box in the {x} direction. (Grasshopper X [item]).
        y: Domain of the box in the {y} direction. (Grasshopper Y [item]).
        z: Domain of the box in the {z} direction. (Grasshopper Z [item]).

    Outputs:
        box: Resulting box (Grasshopper Box).

    Notes:
        Grasshopper: Surface > Primitive > Domain Box (Box).
        pyhopper decisions: none; the box covers the three domains on the base plane (a backwards
        domain is the same box). Defaults X [-2, 2], Y [-0.5, 0.5], Z [0, 0.25] as in Grasshopper.
    """

    display_name = "Domain Box"
    nickname = "Box"
    gh_guid = "79aa7f47-397c-4d3f-9761-aaf421bb7f5f"

    inputs = [
        InputParam("base", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("x", AtomicInterval, Access.ITEM, default=AtomicInterval(-2.0, 2.0)),
        InputParam("y", AtomicInterval, Access.ITEM, default=AtomicInterval(-0.5, 0.5)),
        InputParam("z", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 0.25)),
    ]
    outputs = [
        OutputParam("box", AtomicBox),
    ]

    def generate(self, base=AtomicPlane.world_xy(), x=AtomicInterval(-2.0, 2.0), y=AtomicInterval(-0.5, 0.5), z=AtomicInterval(0.0, 0.25)):
        mids = [0.5 * (float(domain.start) + float(domain.end)) for domain in (x, y, z)]
        centre = point_on_plane(base, mids[0], mids[1], mids[2])
        return AtomicBox(AtomicPlane(centre, base.normal, base.x_axis), *(abs(float(domain.end) - float(domain.start)) for domain in (x, y, z)))
