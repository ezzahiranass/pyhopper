"""ToPolar - Convert a 3D point to plane polar coordinates (Grasshopper "To Polar")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math

from pyhopper.Utils.Planes import plane_coordinates


class ToPolar(Component):
    """Convert a 3D point to plane polar coordinates.

    Inputs:
        point: 3D point to transcribe (Grasshopper Point [item]).
        system: Plane defining polar coordinate space (Grasshopper System [item]).

    Outputs:
        phi: Planar angle in radians (counter-clockwise starting at the plane X-axis) (Grasshopper Phi).
        theta: Vertical angle in radians (Grasshopper Theta).
        radius: Distance from system origin to point (Grasshopper Radius).

    Notes:
        Grasshopper: Vector > Point > To Polar (Polar).
        pyhopper decisions: in the system plane ``phi`` is the azimuth ``atan2(y, x)``, ``theta``
        the elevation ``atan2(z, sqrt(x² + y²))`` and ``radius`` the distance to the origin — all
        Grasshopper-verified; the origin itself gives three zeros.
    """

    display_name = "To Polar"
    nickname = "Polar"
    gh_guid = "61647ba2-31eb-4921-9632-df81e3286f7d"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("system", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("phi", float),
        OutputParam("theta", float),
        OutputParam("radius", float),
    ]

    def generate(self, point=AtomicPoint.origin(), system=AtomicPlane.world_xy()):
        x, y, z = plane_coordinates(system, point)
        radius = math.sqrt(x * x + y * y + z * z)
        if radius == 0.0:
            return 0.0, 0.0, 0.0
        return math.atan2(y, x), math.atan2(z, math.sqrt(x * x + y * y)), radius
