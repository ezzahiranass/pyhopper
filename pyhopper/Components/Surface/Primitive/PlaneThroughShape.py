"""PlaneThroughShape - Make a rectangular surface that is larger than a given shape (Grasshopper "Plane Through Shape")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Bounds import tight_extents
from pyhopper.Utils.SurfaceBuilders import plane_surface
from pyhopper.Core.TypeSystem import GEOMETRY, SURFACE


class PlaneThroughShape(Component):
    """Make a rectangular surface that is larger than a given shape.

    Inputs:
        plane: Surface plane (Grasshopper Plane [item]).
        shape: Shape to exceed (Grasshopper Shape [item]).
        inflate: Boundary inflation amount (Grasshopper Inflate [item]).

    Outputs:
        surface: Resulting planar surface (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Primitive > Plane Through Shape (PxS).
        pyhopper decisions: Grasshopper-verified — a degree-1 plane surface whose knot domains are the
        shape's extents in the plane's coordinates grown by ``inflate`` on every side (default 1);
        NURBS curves and surfaces are measured tightly by sampling, other atoms exactly. The shape is
        required.
    """

    display_name = "Plane Through Shape"
    nickname = "PxS"
    gh_guid = "d8698126-0e91-4ae7-ba05-2490258573ea"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("shape", GEOMETRY, Access.ITEM),
        InputParam("inflate", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), shape=None, inflate=1.0):
        extents = tight_extents(shape, plane)
        if extents is None:
            raise ValueError("PlaneThroughShape needs a shape with an extent")
        (x0, x1), (y0, y1), _ = extents
        grow = float(inflate)
        return plane_surface(plane, AtomicInterval(x0 - grow, x1 + grow), AtomicInterval(y0 - grow, y1 + grow))
