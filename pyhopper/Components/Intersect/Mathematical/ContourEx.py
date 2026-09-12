"""ContourEx - Create a set of Brep or Mesh contours (Grasshopper "Contour (ex)")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path
from pyhopper.Core.TypeSystem import CURVE, GEOMETRY
from pyhopper.Utils.Intersections import brep_plane_section, cumulative_offsets, offset_plane, shape_faces


class ContourEx(Component):
    """Create a set of Brep or Mesh contours.

    Inputs:
        shape: Brep or Mesh to contour (Grasshopper Shape [item]).
        plane: Base plane for contours (Grasshopper Plane [item]).
        offsets: Contour offsets from base plane (if omitted, you must specify distances instead) (Grasshopper Offsets [list]).
        distances: Distances between contours (if omitted, you must specify offset instead) (Grasshopper Distances [list]).

    Outputs:
        contours: Resulting contours (grouped by section) (Grasshopper Contours).

    Notes:
        Grasshopper: Intersect > Mathematical > Contour (ex) (Contour).
        pyhopper decisions: Grasshopper's rules — offsets win over distances and are used in the order
        given; distances accumulate from the first one (planes at d0, d0+d1, ...); neither raises
        ``ValueError("You either have to specify Distances or Offsets")``. Each plane's section curves land
        in their own branch ``{iteration;k}`` (Grasshopper's path rule for the contour components), empty
        when the plane misses the shape. Breps, surfaces and boxes are supported (meshes wait for the mesh
        kernel).
    """

    display_name = "Contour (ex)"
    nickname = "Contour"
    gh_guid = "246cda78-5e88-4087-ba09-ae082bbc4af8"

    inputs = [
        InputParam("shape", GEOMETRY, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("offsets", float, Access.LIST, optional=True),
        InputParam("distances", float, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("contours", CURVE, access=Access.TREE),
    ]

    def generate(self, shape=None, plane=AtomicPlane.world_xy(), offsets=None, distances=None):
        shape_faces(shape)
        run = self.iteration.run if self.iteration else 0
        planes = [offset_plane(plane, offset) for offset in cumulative_offsets(offsets, distances)]
        return DataTree.from_branches({Path(run, k): brep_plane_section(shape, section_plane) for k, section_plane in enumerate(planes)})
