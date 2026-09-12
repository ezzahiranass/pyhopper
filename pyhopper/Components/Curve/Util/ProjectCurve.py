"""ProjectCurve - Project a curve onto a Brep (Grasshopper "Project Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBrep, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurvesOnSurfaces import project_curve
from pyhopper.Core.TypeSystem import CURVE


class ProjectCurve(Component):
    """Project a curve onto a Brep.

    Inputs:
        curve: Curve to project (Grasshopper Curve [item]).
        brep: Brep to project onto (Grasshopper Brep [item]).
        direction: Projection direction (Grasshopper Direction [item]).

    Outputs:
        curve: Projected curves (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Project Curve (Project).
        pyhopper decisions: Grasshopper-verified in structure — the curve's samples are projected along
        the direction (either way, default +z) onto the nearest face hit and the runs of hits are
        interpolated (straight runs become lines), with run ends refined to the face edges; Rhino
        computes the exact projection, so only the count and extent of the curves compare. A zero
        direction raises ``ValueError``.
    """

    display_name = "Project Curve"
    nickname = "Project"
    gh_guid = "d7ee52ff-89b8-4d1a-8662-3e0dd391d0af"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("brep", AtomicBrep, Access.ITEM),
        InputParam("direction", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
    ]
    outputs = [
        OutputParam("curve", CURVE, access=Access.LIST),
    ]

    def generate(self, curve=None, brep=None, direction=AtomicVector.unit_z()):
        return project_curve(curve, brep, direction)
