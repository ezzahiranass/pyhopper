"""Explode - Explode a curve into smaller segments (Grasshopper "Explode")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import explode
from pyhopper.Core.TypeSystem import CURVE


class Explode(Component):
    """Explode a curve into smaller segments.

    Inputs:
        curve: Curve to explode (Grasshopper Curve [item]).
        recursive: Recursive decomposition until all segments are atomic (Grasshopper Recursive [item]).

    Outputs:
        segments: Exploded segments that make up the base curve (Grasshopper Segments).
        vertices: Vertices of the exploded segments (Grasshopper Vertices).

    Notes:
        Grasshopper: Curve > Util > Explode (Explode).
        pyhopper decisions: Grasshopper-verified — polylines explode into lines, NURBS curves split at
        their kinks (interior knots of full multiplicity), polycurves into their segments (nested
        polylines and polycurves exploded too when ``recursive``, the default), smooth curves come back
        whole; the vertices are the segment ends, the start repeated for closed curves.
    """

    display_name = "Explode"
    nickname = "Explode"
    gh_guid = "afb96615-c59a-45c9-9cac-e27acb1c7ca0"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("recursive", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("segments", CURVE, access=Access.LIST),
        OutputParam("vertices", AtomicPoint, access=Access.LIST),
    ]

    def generate(self, curve=None, recursive=True):
        return explode(curve, bool(recursive))
