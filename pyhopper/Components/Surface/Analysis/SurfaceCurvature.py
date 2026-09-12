"""SurfaceCurvature - Evaluate the surface curvature at a {uv} coordinate (Grasshopper "Surface Curvature")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import surface_analysis
from pyhopper.Core.TypeSystem import SURFACE


class SurfaceCurvature(Component):
    """Evaluate the surface curvature at a {uv} coordinate.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        point: {uv} coordinate to evaluate (Grasshopper Point [item]).

    Outputs:
        frame: Surface frame at {uv} coordinate (Grasshopper Frame).
        gaussian: Gaussian curvature (Grasshopper Gaussian).
        mean: Mean curvature (Grasshopper Mean).

    Notes:
        Grasshopper: Surface > Analysis > Surface Curvature (Curvature).
        pyhopper decisions: Grasshopper-verified — Gaussian and mean curvature from the fundamental
        forms with the normal ``Su × Sv`` (a dome bending away from its normal has negative mean
        curvature), plus the surface frame; ``point`` carries the (u, v) coordinate in its x and y.
    """

    display_name = "Surface Curvature"
    nickname = "Curvature"
    gh_guid = "4139f3a3-cf93-4fc0-b5e0-18a3acd0b003"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
    ]
    outputs = [
        OutputParam("frame", AtomicPlane),
        OutputParam("gaussian", float),
        OutputParam("mean", float),
    ]

    def generate(self, surface=None, point=AtomicPoint.origin()):
        analysis = surface_analysis(surface, point.x, point.y)
        return analysis.frame, analysis.gaussian, analysis.mean
