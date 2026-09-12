"""InterpolateData - Interpolate a collection of data (Grasshopper "Interpolate data")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Utils.Vectors import lerp

from .._arith import Spatial, is_number


class InterpolateData(Component):
    """Interpolate a collection of data.

    Inputs:
        data: Data to interpolate (simple data types only). (Grasshopper Data [list]).
        parameter: Normalised interpolation parameter. (Grasshopper Parameter [item]).

    Outputs:
        value: Interpolated value. (Grasshopper Value).

    Notes:
        Grasshopper: Maths > Util > Interpolate data (Interp).
        pyhopper decisions: linear interpolation along the list — ``t`` in [0, 1] is clamped and
        maps to index ``t * (n - 1)`` (Grasshopper-verified); numbers, vectors, points and domains
        interpolate, integers and booleans round to the nearest even integer like Grasshopper, a
        single value is returned as is. An empty list or unsupported data raises.
    """

    display_name = "Interpolate data"
    nickname = "Interp"
    gh_guid = "e168ff6b-e5c0-48f1-b831-f6996bf3b459"

    inputs = [
        InputParam("data", None, Access.LIST),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("value"),
    ]

    def generate(self, data=None, parameter=0.0):
        items = list(data or [])
        if not items:
            raise ValueError("InterpolateData needs at least one value")
        if len(items) == 1:
            return items[0]
        position = min(max(float(parameter), 0.0), 1.0) * (len(items) - 1)
        index = min(int(position), len(items) - 2)
        t = position - index
        a, b = items[index], items[index + 1]
        if isinstance(a, (bool, int)) and isinstance(b, (bool, int)):
            return round(int(a) + (int(b) - int(a)) * t)
        if is_number(a) and is_number(b):
            return float(a) + (float(b) - float(a)) * t
        if isinstance(a, Spatial) and isinstance(b, Spatial):
            return lerp(a, b, t)
        if isinstance(a, AtomicInterval) and isinstance(b, AtomicInterval):
            return AtomicInterval(a.start + (b.start - a.start) * t, a.end + (b.end - a.end) * t)
        raise TypeError("InterpolateData handles numbers, vectors, points and domains only")
