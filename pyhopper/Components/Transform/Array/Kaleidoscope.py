"""Kaleidoscope - Apply a kaleidoscope transformation to an object (Grasshopper "Kaleidoscope")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._geometry import geometry_centre, kaleidoscope_transforms
from ._helpers import array_result
from pyhopper.Core.TypeSystem import GEOMETRY


class Kaleidoscope(Component):
    """Apply a kaleidoscope transformation to an object.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        plane: Kaleidoscope plane (Grasshopper Plane [item]).
        segments: Kaleidoscope segments. (Grasshopper Segments [item]).

    Outputs:
        geometry: Mirrored geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Array > Kaleidoscope (KScope).
        pyhopper decisions: Grasshopper-verified — ``segments`` images including the original: even
        images rotate by k·2π/S about the plane normal, odd images mirror across the line through the
        plane origin at the geometry's own angle plus k·π/S (the geometry's bounding-box centre sets the
        angle), so the images tile the plane like a kaleidoscope. Fewer than one segment raises.
        Default 10.
    """

    display_name = "Kaleidoscope"
    nickname = "KScope"
    gh_guid = "b90eaa92-6e38-4054-a915-afcf486224b3"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM, optional=True),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("segments", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY, access=Access.LIST),
        OutputParam("transform", AtomicTransform, access=Access.LIST),
    ]

    def generate(self, geometry=None, plane=AtomicPlane.world_xy(), segments=10):
        if geometry is None:
            return Component.NO_OUTPUT, kaleidoscope_transforms(plane, int(segments), plane.origin)
        return array_result(geometry, kaleidoscope_transforms(plane, int(segments), geometry_centre(geometry)))
