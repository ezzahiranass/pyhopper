"""PrincipalCurvature - Evaluate the principal curvature of a surface at a {uv} coordinate (Grasshopper "Principal Curvature")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import surface_analysis
from pyhopper.Core.TypeSystem import SURFACE


class PrincipalCurvature(Component):
    """Evaluate the principal curvature of a surface at a {uv} coordinate.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        point: {uv} coordinate to evaluate (Grasshopper Point [item]).

    Outputs:
        frame: Surface frame at (uv) coordinate (Grasshopper Frame).
        maximum: Maximum (absolute) principal curvature (Grasshopper Maximum).
        minimum: Minimum (absolute) principal curvature (Grasshopper Minimum).
        max_direction: Principal curvature direction corresponding to C¹. (Grasshopper Max direction).
        min_direction: Principal curvature direction corresponding to C². (Grasshopper Min direction).

    Notes:
        Grasshopper: Surface > Analysis > Principal Curvature (Curvature).
        pyhopper decisions: Grasshopper-verified — ``maximum`` is the principal curvature of larger
        absolute value (ties go to the algebraically larger one), ``minimum`` the other; directions are
        unit vectors in the tangent plane whose sign is arbitrary (Grasshopper's own signs vary);
        umbilic points use the U and V directions. ``point`` carries the (u, v) coordinate in its x and y.
    """

    display_name = "Principal Curvature"
    nickname = "Curvature"
    gh_guid = "404f75ac-5594-4c48-ad8a-7d0f472bbf8a"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
    ]
    outputs = [
        OutputParam("frame", AtomicPlane),
        OutputParam("maximum", float),
        OutputParam("minimum", float),
        OutputParam("max_direction", AtomicVector),
        OutputParam("min_direction", AtomicVector),
    ]

    def generate(self, surface=None, point=AtomicPoint.origin()):
        analysis = surface_analysis(surface, point.x, point.y)
        return analysis.frame, analysis.maximum, analysis.minimum, analysis.max_direction, analysis.min_direction
