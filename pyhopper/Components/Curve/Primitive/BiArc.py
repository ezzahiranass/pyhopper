"""BiArc - Create a bi-arc based on endpoints and tangents (Grasshopper "BiArc")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicArc, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Tangency import biarc
from pyhopper.Core.TypeSystem import CURVE


class BiArc(Component):
    """Create a bi-arc based on endpoints and tangents.

    Inputs:
        start_point: Start point of bi-arc. (Grasshopper Start Point [item]).
        start_tangent: Tangent vector at start of bi-arc. (Grasshopper Start Tangent [item]).
        end_point: End point of bi-arc. (Grasshopper End Point [item]).
        end_tangent: Tangent vector at end of bi-arc. (Grasshopper End Tangent [item]).
        ratio: Ratio of bi-arc segment weight (Grasshopper Ratio [item]).

    Outputs:
        first_arc: First segment of bi-arc curve (Grasshopper First arc).
        second_arc: Second segment of bi-arc curve (Grasshopper Second arc).
        bi_arc: Resulting bi-arc. (Grasshopper Bi-Arc).

    Notes:
        Grasshopper: Curve > Primitive > BiArc (BiArc).
        pyhopper decisions: tangents are unitised (Grasshopper ignores their length); the two arcs'
        tangent lengths are split ``ratio : 1 - ratio``, which reproduces Grasshopper exactly at its
        default 0.5 (the equal-tangent biarc); other ratios move the joint along the same biarc family
        as Grasshopper but through a different parametrisation. The second arc is stored Rhino's way
        (x axis at the end point, negative start angle); co-circular arcs collapse to one arc for the
        Bi-Arc output, otherwise it is the two-arc polycurve on arc-length spans. A degenerate
        (straight) arc or a ratio outside (0, 1) raises ``ValueError``. Points and tangents are
        required.
    """

    display_name = "BiArc"
    nickname = "BiArc"
    gh_guid = "75f4b0fd-9721-47b1-99e7-9c098b342e67"

    inputs = [
        InputParam("start_point", AtomicPoint, Access.ITEM),
        InputParam("start_tangent", AtomicVector, Access.ITEM),
        InputParam("end_point", AtomicPoint, Access.ITEM),
        InputParam("end_tangent", AtomicVector, Access.ITEM),
        InputParam("ratio", float, Access.ITEM, default=0.5),
    ]
    outputs = [
        OutputParam("first_arc", AtomicArc),
        OutputParam("second_arc", AtomicArc),
        OutputParam("bi_arc", CURVE),
    ]

    def generate(self, start_point, start_tangent, end_point, end_tangent, ratio=0.5):
        return biarc(start_point, start_tangent, end_point, end_tangent, float(ratio))
