"""CurveContour - Create a set of Curve contours (Grasshopper "Curve Contour")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Curves import curve_is_closed
from pyhopper.Utils.Intersections import contour_offsets, curve_plane_intersections, extent_along, offset_plane
from pyhopper.Utils.Planes import plane_from_normal
from pyhopper.Utils.Tolerances import ABSOLUTE_TOLERANCE
from pyhopper.Utils.Vectors import is_zero, negate


class CurveContour(Component):
    """Create a set of Curve contours.

    Inputs:
        curve: Curve to contour (Grasshopper Curve [item]).
        point: Contour start point (Grasshopper Point [item]).
        direction: Contour normal direction (Grasshopper Direction [item]).
        distance: Distance between contours (Grasshopper Distance [item]).

    Outputs:
        contours: Resulting contour points (grouped by section) (Grasshopper Contours).
        parameters: Curve parameters for all contour points (Grasshopper Parameters).

    Notes:
        Grasshopper: Curve > Division > Curve Contour (Contour).
        pyhopper decisions: Grasshopper-verified — contour planes at ``point + k·distance·direction``
        for every integer k with the curve's extent along the direction as ``min <= offset < max``
        (negative k included; a negative distance walks the other way), ascending; each plane's points
        and native parameters land in their own branch ``{iteration;k}`` — Grasshopper's path rule for
        the contour components, which uses the running iteration count rather than the input path. A
        closed curve crossing a plane at its seam reports the seam at both its start and end parameter,
        as Grasshopper does. A distance within the absolute tolerance raises ``ValueError`` with
        Grasshopper's message; Grasshopper has no default distance, pyhopper uses 1.0.
    """

    display_name = "Curve Contour"
    nickname = "Contour"
    gh_guid = "88cff285-7f5e-41b3-96d5-9588ff9a52b1"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("direction", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
        InputParam("distance", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("contours", AtomicPoint, access=Access.TREE),
        OutputParam("parameters", float, access=Access.TREE),
    ]

    def generate(self, curve=None, point=AtomicPoint.origin(), direction=AtomicVector.unit_z(), distance=1.0):
        if is_zero(direction):
            raise ValueError("Contour direction must not be a zero vector")
        if abs(distance) <= ABSOLUTE_TOLERANCE:
            raise ValueError("Contour distance must be larger than the document absolute tolerance")
        if distance < 0:
            direction, distance = negate(direction), -distance
        base = plane_from_normal(point, direction)
        offsets = contour_offsets(extent_along(curve, point, direction), 0.0, distance)
        run = self.iteration.run if self.iteration else 0
        seam_twice = curve_is_closed(curve)
        points: dict[Path, list] = {}
        parameters: dict[Path, list] = {}
        for k, offset in enumerate(offsets):
            events = curve_plane_intersections(curve, offset_plane(base, offset), seam_twice=seam_twice)
            points[Path(run, k)] = [p for _, p in events]
            parameters[Path(run, k)] = [t for t, _ in events]
        return DataTree.from_branches(points), DataTree.from_branches(parameters)
