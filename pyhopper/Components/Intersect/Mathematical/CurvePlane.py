"""CurvePlane - Solve intersection events for a curve and a plane (Grasshopper "Curve | Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import curve_plane_intersections
from pyhopper.Utils.Planes import plane_coordinates


class CurvePlane(Component):
    """Solve intersection events for a curve and a plane.

    Inputs:
        curve: Base curve (Grasshopper Curve [item]).
        plane: Intersection plane (Grasshopper Plane [item]).

    Outputs:
        points: Intersection events (Grasshopper Points).
        params_c: Parameters {t} on curve (Grasshopper Params C).
        params_p: Parameters {uv} on plane (Grasshopper Params P).

    Notes:
        Grasshopper: Intersect > Mathematical > Curve | Plane (PCX).
        pyhopper decisions: Grasshopper-verified — crossings, touches and both ends of a stretch lying in
        the plane, sorted by curve parameter; the seam of a closed curve is one event at its start
        parameter. ``params_c`` are the curve's native parameters (reparametrize the input for [0, 1]),
        ``params_p`` the plane coordinates of each point as ``(u, v, 0)``. Coincidence uses pyhopper's
        absolute tolerance (0.01, Rhino's default document tolerance that Grasshopper uses). Grasshopper has
        no default plane; pyhopper uses the world XY plane.
    """

    display_name = "Curve | Plane"
    nickname = "PCX"
    gh_guid = "b7c12ed1-b09a-4e15-996f-3fa9f3f16b1c"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("params_c", float, access=Access.LIST),
        OutputParam("params_p", AtomicPoint, access=Access.LIST),
    ]

    def generate(self, curve=None, plane=AtomicPlane.world_xy()):
        events = curve_plane_intersections(curve, plane)
        points = [point for _, point in events]
        uv = [AtomicPoint(u, v, 0.0) for u, v, _ in (plane_coordinates(plane, point) for point in points)]
        return points, [t for t, _ in events], uv
