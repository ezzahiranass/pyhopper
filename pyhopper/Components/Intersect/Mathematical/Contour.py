"""Contour - Create a set of Brep or Mesh contours (Grasshopper "Contour")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path
from pyhopper.Core.TypeSystem import CURVE, GEOMETRY
from pyhopper.Utils.Intersections import brep_plane_section, contour_offsets, extent_along, offset_plane, shape_faces
from pyhopper.Utils.Planes import plane_from_normal
from pyhopper.Utils.Tolerances import ABSOLUTE_TOLERANCE
from pyhopper.Utils.Vectors import is_zero, negate


class Contour(Component):
    """Create a set of Brep or Mesh contours.

    Inputs:
        shape: Brep or Mesh to contour (Grasshopper Shape [item]).
        point: Contour start point (Grasshopper Point [item]).
        direction: Contour normal direction (Grasshopper Direction [item]).
        distance: Distance between contours (Grasshopper Distance [item]).

    Outputs:
        contours: Resulting contours (grouped by section) (Grasshopper Contours).

    Notes:
        Grasshopper: Intersect > Mathematical > Contour (Contour).
        pyhopper decisions: section planes at ``point + k·distance·direction`` for every integer k with the
        shape's extent along the direction as ``min <= offset < max`` (negative k included; a negative
        distance walks the other way), ascending; each plane's section curves land in their own branch
        ``{iteration;k}`` — Grasshopper's own path rule for this component, which uses the running iteration
        count rather than the input path — empty when a plane misses the shape. Breps, surfaces and boxes
        are supported (meshes wait for the mesh kernel); a distance within the absolute tolerance raises
        ``ValueError`` like Grasshopper's error. Grasshopper has no default distance; pyhopper uses 1.0.
    """

    display_name = "Contour"
    nickname = "Contour"
    gh_guid = "3b112fb6-3eba-42d2-ba75-0f903c18faab"

    inputs = [
        InputParam("shape", GEOMETRY, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("direction", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
        InputParam("distance", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("contours", CURVE, access=Access.TREE),
    ]

    def generate(self, shape=None, point=AtomicPoint.origin(), direction=AtomicVector.unit_z(), distance=1.0):
        shape_faces(shape)
        if is_zero(direction):
            raise ValueError("Contour direction must not be a zero vector")
        if abs(distance) <= ABSOLUTE_TOLERANCE:
            raise ValueError("Contour distance must be larger than the document absolute tolerance")
        if distance < 0:
            direction, distance = negate(direction), -distance
        base = plane_from_normal(point, direction)
        offsets = contour_offsets(extent_along(shape, point, direction), 0.0, distance)
        run = self.iteration.run if self.iteration else 0
        sections = {Path(run, k): brep_plane_section(shape, offset_plane(base, offset)) for k, offset in enumerate(offsets)}
        return DataTree.from_branches(sections)
