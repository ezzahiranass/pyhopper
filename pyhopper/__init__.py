"""
pyhopper - Declarative parametric 3D modeling in Python.

A Grasshopper-inspired framework with DataTree-based data flow.
"""

# Core data model
from .Core import (
    Path, Branch, DataTree, MatchRule,
    Atom, ATOM_REGISTRY,
    AtomicPoint, AtomicVector, AtomicPlane, AtomicInterval,
    AtomicLine, AtomicCircle, AtomicArc, AtomicPolyline, AtomicNurbsCurve,
    AtomicMesh, AtomicSurface, AtomicCylinder,
    AtomicBrep, AtomicTransform,
    Component, ComponentResult, Access, InputParam, OutputParam,
)

# Components — re-exported with user-friendly names
from .Components.Maths.Series import Series
from .Components.Vector.Vector.UnitX import UnitX
from .Components.Vector.Vector.UnitY import UnitY
from .Components.Vector.Vector.UnitZ import UnitZ
from .Components.Vector.Plane.ConstructPlane import ConstructPlane
from .Components.Curve.Primitive.Circle import Circle as CircleCmp
from .Components.Curve.Primitive.Line import Line as LineCmp
from .Components.Curve.Primitive.Polygon import Polygon
from .Components.Curve.Primitive.Cylinder import Cylinder as CylinderCmp
from .Components.Curve.Analysis.CurveMiddle import CurveMiddle
from .Components.Curve.Division.DivideCurve import DivideCurve
from .Components.Curve.Spline.TweenCurve import TweenCurve
from .Components.Surface.Freeform.Extrude import Extrude
from .Components.Surface.Freeform.RuledSurface import RuledSurface
from .Components.Transform.Euclidian.Move import Move
from .Components.Transform.Euclidian.Rotate import Rotate
from .Components.Transform.Euclidian.Mirror import Mirror
from .Components.Sets.List.ListItem import ListItem
from .Components.Sets.Sequence.Range import Range
from .Components.Sets.Tree.Merge import Merge
from .Components.Params.Geometry.Curve import Curve
from .Components.Params.Geometry.Geometry import Geometry
from .Components.Params.Geometry.Point import Point
from .Components.Params.Input.NumberSlider import NumberSlider
from .Components.Params.Input.Panel import Panel

from .admin_utils import list_components

__all__ = [
    # Core
    "Path", "Branch", "DataTree", "MatchRule",
    "Atom", "ATOM_REGISTRY",
    "AtomicPoint", "AtomicVector", "AtomicPlane", "AtomicInterval",
    "AtomicLine", "AtomicCircle", "AtomicArc", "AtomicPolyline", "AtomicNurbsCurve",
    "AtomicMesh", "AtomicSurface", "AtomicCylinder",
    "AtomicBrep", "AtomicTransform",
    "Component", "ComponentResult", "Access", "InputParam", "OutputParam",

    # Components
    "Series", "UnitX", "UnitY", "UnitZ", "ConstructPlane",
    "CircleCmp", "LineCmp", "Polygon", "CylinderCmp",
    "CurveMiddle", "DivideCurve", "TweenCurve",
    "Extrude", "RuledSurface", "Move", "Rotate", "Mirror",
    "ListItem", "Range", "Merge", "Curve", "Geometry", "Point", "NumberSlider", "Panel",
    
    "list_components",
]
