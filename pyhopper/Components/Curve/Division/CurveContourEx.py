"""CurveContourEx - Create a set of Curve contours (Grasshopper "Contour (ex)")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Curves import curve_is_closed
from pyhopper.Utils.Intersections import cumulative_offsets, curve_plane_intersections, offset_plane


class CurveContourEx(Component):
    """Create a set of Curve contours.

    Inputs:
        curve: Curve to contour (Grasshopper Curve [item]).
        plane: Base plane for contours (Grasshopper Plane [item]).
        offsets: Contour offsets from base plane (if omitted, you must specify distances instead) (Grasshopper Offsets [list]).
        distances: Distances between contours (if omitted, you must specify offset instead) (Grasshopper Distances [list]).

    Outputs:
        contours: Resulting contour points (grouped by section) (Grasshopper Contours).
        parameters: Curve parameters for all contour points (Grasshopper Parameters).

    Notes:
        Grasshopper: Curve > Division > Contour (ex) (Contour).
        pyhopper decisions: Grasshopper-verified — offsets win over distances and are used in the
        order given; distances accumulate from the first one (planes at d0, d0+d1, ...); neither raises
        ``ValueError("You either have to specify Distances or Offsets")``. Each plane's points and native
        parameters land in their own branch ``{iteration;k}`` (Grasshopper's path rule for the contour
        components), empty when the plane misses the curve. A closed curve crossing a plane at its seam
        reports the seam at both its start and end parameter, as Grasshopper does.
    """

    display_name = "Contour (ex)"
    nickname = "Contour"
    gh_guid = "3e7e4827-6edd-4e10-93ac-cc234414d2b9"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("offsets", float, Access.LIST, optional=True),
        InputParam("distances", float, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("contours", AtomicPoint, access=Access.TREE),
        OutputParam("parameters", float, access=Access.TREE),
    ]

    def generate(self, curve=None, plane=AtomicPlane.world_xy(), offsets=None, distances=None):
        run = self.iteration.run if self.iteration else 0
        seam_twice = curve_is_closed(curve)
        points: dict[Path, list] = {}
        parameters: dict[Path, list] = {}
        for k, offset in enumerate(cumulative_offsets(offsets, distances)):
            events = curve_plane_intersections(curve, offset_plane(plane, offset), seam_twice=seam_twice)
            points[Path(run, k)] = [p for _, p in events]
            parameters[Path(run, k)] = [t for t, _ in events]
        return DataTree.from_branches(points), DataTree.from_branches(parameters)
