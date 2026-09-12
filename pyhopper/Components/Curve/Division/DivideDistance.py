"""DivideDistance - Divide a curve at fixed arc-length intervals."""

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import divide_nurbs_curve_by_distance
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


class DivideDistance(Component):
    """Divide a curve into points separated by a preset arc-length distance."""

    inputs = [
        InputParam("curve", None, Access.ITEM),
        InputParam("distance", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("tangents", AtomicVector, access=Access.LIST),
        OutputParam("parameters", float, access=Access.LIST),
    ]

    def generate(self, curve=None, distance=1.0):
        return divide_nurbs_curve_by_distance(as_nurbs_curve(curve), float(distance))
