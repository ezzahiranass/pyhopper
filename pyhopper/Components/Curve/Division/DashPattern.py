"""DashPattern - Convert a curve to a dash pattern (Grasshopper "Dash Pattern")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import dash_pattern
from pyhopper.Core.TypeSystem import CURVE


class DashPattern(Component):
    """Convert a curve to a dash pattern.

    Inputs:
        curve: Curve to dash (Grasshopper Curve [item]).
        pattern: An collection of dash and gap lengths. (Grasshopper Pattern [list]).

    Outputs:
        dashes: Dash segments (Grasshopper Dashes).
        gaps: Gap segments (Grasshopper Gaps).

    Notes:
        Grasshopper: Curve > Division > Dash Pattern (Dash).
        pyhopper decisions: Grasshopper-verified — the pattern lengths are walked along the curve,
        alternating dashes and gaps (an odd pattern swaps roles every cycle), the last piece cut at the
        curve end; pieces keep the input's type. Negative lengths raise ``ValueError`` (Grasshopper
        reports an error), zero-length pieces are skipped (Grasshopper emits nulls), an empty pattern
        gives nothing.
    """

    display_name = "Dash Pattern"
    nickname = "Dash"
    gh_guid = "95866bbe-648e-4e2b-a97c-7d04679e94e0"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("pattern", float, Access.LIST),
    ]
    outputs = [
        OutputParam("dashes", CURVE, access=Access.LIST),
        OutputParam("gaps", CURVE, access=Access.LIST),
    ]

    def generate(self, curve=None, pattern=None):
        return dash_pattern(curve, list(pattern or []))
