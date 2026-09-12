"""EvaluateSurface - Evaluate local surface properties at a {uv} coordinate (Grasshopper "Evaluate Surface")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import surface_analysis
from pyhopper.Core.TypeSystem import SURFACE


class EvaluateSurface(Component):
    """Evaluate local surface properties at a {uv} coordinate.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        point: {uv} coordinate to evaluate (Grasshopper Point [item]).

    Outputs:
        point: Point at {uv} (Grasshopper Point).
        normal: Normal at {uv} (Grasshopper Normal).
        u_direction: U direction at {uv} (Grasshopper U direction).
        v_direction: V direction at {uv} (Grasshopper V direction).
        frame: Frame at {uv} (Grasshopper Frame).

    Notes:
        Grasshopper: Surface > Analysis > Evaluate Surface (EvalSrf).
        pyhopper decisions: Grasshopper-verified — point, unit normal (``Su × Sv``), unit U and V
        directions and the frame (origin at the point, x along U, normal along the surface normal);
        ``point`` carries the (u, v) coordinate in its x and y; a degenerate normal raises ``ValueError``.
    """

    display_name = "Evaluate Surface"
    nickname = "EvalSrf"
    gh_guid = "353b206e-bde5-4f02-a913-b3b8a977d4b9"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("normal", AtomicVector),
        OutputParam("u_direction", AtomicVector),
        OutputParam("v_direction", AtomicVector),
        OutputParam("frame", AtomicPlane),
    ]

    def generate(self, surface=None, point=AtomicPoint.origin()):
        analysis = surface_analysis(surface, point.x, point.y)
        return analysis.point, analysis.normal, analysis.u_direction, analysis.v_direction, analysis.frame
