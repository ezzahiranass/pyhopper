"""BrepPlane - Solve intersection events for a Brep and a plane (otherwise known as section) (Grasshopper "Brep | Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBrep, AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import brep_plane_section


class BrepPlane(Component):
    """Solve intersection events for a Brep and a plane (otherwise known as section).

    Inputs:
        brep: Base Brep (Grasshopper Brep [item]).
        plane: Section plane (Grasshopper Plane [item]).

    Outputs:
        curves: Section curves (Grasshopper Curves).
        points: Section points (Grasshopper Points).

    Notes:
        Grasshopper: Intersect > Mathematical > Brep | Plane (Sec).
        pyhopper decisions: section curves per face, joined end to end (closed sections of planar
        faces become polylines, curved faces interpolated curves through the marching-squares section
        refined onto the plane; a face lying in the plane contributes its boundary once). ``points`` —
        Grasshopper's isolated touch points — is always empty. Boxes and surfaces are accepted as breps.
    """

    display_name = "Brep | Plane"
    nickname = "Sec"
    gh_guid = "4fe828e8-fa95-4cc5-9a8c-c33856ecc783"

    inputs = [
        InputParam("brep", AtomicBrep, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("curves", CURVE, access=Access.LIST),
        OutputParam("points", AtomicPoint, access=Access.LIST),
    ]

    def generate(self, brep=None, plane=AtomicPlane.world_xy()):
        return brep_plane_section(brep, plane), []
