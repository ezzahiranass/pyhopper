"""
pyhopper - Declarative parametric 3D modeling in Python.

A Grasshopper-inspired framework with DataTree-based data flow.
"""

# Core data model
from .Core import (
    Path, Branch, DataTree, MatchRule,
    Atom, ATOM_REGISTRY, atom_from_json,
    AtomicPoint, AtomicVector, AtomicPlane, AtomicInterval,
    AtomicLine, AtomicCircle, AtomicArc, AtomicPolyline, AtomicNurbsCurve,
    AtomicEllipse, AtomicRectangle, AtomicBox, AtomicInterpolatedCurve, AtomicControlPointCurve,
    AtomicMesh, AtomicSurface, AtomicTrimmedSurface, AtomicCylinder,
    AtomicBrep, AtomicTransform,
    Component, ComponentResult, Access, InputParam, OutputParam,
    CURVE, GEOMETRY, SURFACE, CURVE_TYPES, GEOMETRY_TYPES,
    CoercionError, TypeSpec, accepted_type_names, coerce_item, coerce_tree, type_name,
)

# Components — re-exported with user-friendly names
from .Components.Maths.Series import Series
from .Components.Maths.Domain.Bounds import Bounds
from .Components.Maths.Domain.ConstructDomain import ConstructDomain
from .Components.Maths.Domain.DeconstructDomain import DeconstructDomain
from .Components.Vector.Point.ConstructPoint import ConstructPoint
from .Components.Vector.Point.DeconstructPoint import DeconstructPoint
from .Components.Vector.Point.Distance import Distance
from .Components.Vector.Vector.UnitX import UnitX
from .Components.Vector.Vector.UnitY import UnitY
from .Components.Vector.Vector.UnitZ import UnitZ
from .Components.Vector.Vector.Vector2Pt import Vector2Pt
from .Components.Vector.Plane.ConstructPlane import ConstructPlane
from .Components.Vector.Plane.XYPlane import XYPlane
from .Components.Vector.Plane.XZPlane import XZPlane
from .Components.Vector.Plane.YZPlane import YZPlane
from .Components.Curve.Primitive.Circle import Circle as CircleCmp
from .Components.Curve.Primitive.Ellipse import Ellipse
from .Components.Curve.Primitive.Line import Line as LineCmp
from .Components.Curve.Primitive.Polygon import Polygon
from .Components.Curve.Primitive.Cylinder import Cylinder as CylinderCmp
from .Components.Curve.Analysis.CurveMiddle import CurveMiddle
from .Components.Curve.Analysis.Length import Length
from .Components.Curve.Analysis.PointOnCurve import PointOnCurve
from .Components.Curve.Division.DivideCurve import DivideCurve
from .Components.Curve.Division.DivideDistance import DivideDistance
from .Components.Curve.Spline.Interpolate import Interpolate
from .Components.Curve.Spline.TweenCurve import TweenCurve
from .Components.Curve.Spline.NurbsCurve import NurbsCurve
from .Components.Curve.Spline.Polyline import Polyline
from .Components.Curve.Util.OffsetCurve import OffsetCurve
from .Components.Intersect.Shape.RegionDifference import RegionDifference
from .Components.Intersect.Shape.RegionIntersection import RegionIntersection
from .Components.Intersect.Shape.RegionUnion import RegionUnion
from .Components.Surface.Freeform.BoundarySurfaces import BoundarySurfaces
from .Components.Surface.Freeform.Extrude import Extrude
from .Components.Surface.Freeform.FourPointSurface import FourPointSurface
from .Components.Surface.Freeform.Loft import Loft
from .Components.Surface.Freeform.RuledSurface import RuledSurface
from .Components.Surface.Analysis.Area import Area
from .Components.Surface.Analysis.Volume import Volume
from .Components.Surface.Primitive.CenterBox import CenterBox
from .Components.Surface.Primitive.Cone import Cone
from .Components.Surface.Primitive.Cylinder import Cylinder
from .Components.Surface.Primitive.Sphere import Sphere
from .Components.Transform.Affine.Scale import Scale
from .Components.Transform.Affine.ScaleNU import ScaleNU
from .Components.Transform.Array.BoxArray import BoxArray
from .Components.Transform.Array.CurveArray import CurveArray
from .Components.Transform.Array.LinearArray import LinearArray
from .Components.Transform.Array.PolarArray import PolarArray
from .Components.Transform.Array.RectangularArray import RectangularArray
from .Components.Transform.Euclidian.Move import Move
from .Components.Transform.Euclidian.Orient import Orient
from .Components.Transform.Euclidian.Rotate import Rotate
from .Components.Transform.Euclidian.RotateAxis import RotateAxis
from .Components.Transform.Euclidian.Mirror import Mirror
from .Components.Sets.List.ListItem import ListItem
from .Components.Sets.List.ListLength import ListLength
from .Components.Sets.List.PartitionList import PartitionList
from .Components.Sets.List.ReverseList import ReverseList
from .Components.Sets.List.ShiftList import ShiftList
from .Components.Sets.List.SplitList import SplitList
from .Components.Sets.List.SubList import SubList
from .Components.Sets.Sequence.CullIndex import CullIndex
from .Components.Sets.Sequence.Range import Range
from .Components.Sets.Sequence.Random import Random
from .Components.Sets.Tree.Merge import Merge
from .Components.Sets.Text.Characters import Characters
from .Components.Sets.Text.Concatenate import Concatenate
from .Components.Sets.Text.ReplaceText import ReplaceText
from .Components.Sets.Text.TextCase import TextCase
from .Components.Sets.Text.TextLength import TextLength
from .Components.Sets.Text.TextSplit import TextSplit
from .Components.Params.Geometry.Curve import Curve
from .Components.Params.Geometry.Geometry import Geometry
from .Components.Params.Geometry.Point import Point
from .Components.Params.Geometry.Box import Box as BoxParam
from .Components.Params.Geometry.Brep import Brep as BrepParam
from .Components.Params.Geometry.Circle import Circle as CircleParam
from .Components.Params.Geometry.Line import Line as LineParam
from .Components.Params.Geometry.Plane import Plane as PlaneParam
from .Components.Params.Geometry.Rectangle import Rectangle as RectangleParam
from .Components.Params.Geometry.Surface import Surface as SurfaceParam
from .Components.Params.Geometry.Transform import Transform as TransformParam
from .Components.Params.Geometry.Vector import Vector as VectorParam
from .Components.Params.Primitive.Boolean import Boolean
from .Components.Params.Primitive.Domain import Domain
from .Components.Params.Primitive.Integer import Integer
from .Components.Params.Primitive.Number import Number
from .Components.Params.Primitive.Text import Text
from .Components.Params.Input.BooleanToggle import BooleanToggle
from .Components.Params.Input.GraphMapper import GraphMapper
from .Components.Params.Input.MDSlider import MDSlider
from .Components.Params.Input.NumberSlider import NumberSlider
from .Components.Params.Input.Panel import Panel

from .admin_utils import list_components
from .Graph import (
    CompiledGraph, GraphCompilerValidationError, PORT_OP_METHODS,
    VALID_PORT_OPERATIONS, compile_graph_document, execute_compiled_graph,
    serialize_preview_value,
)

__all__ = [
    # Core
    "Path", "Branch", "DataTree", "MatchRule",
    "Atom", "ATOM_REGISTRY", "atom_from_json",
    "AtomicPoint", "AtomicVector", "AtomicPlane", "AtomicInterval",
    "AtomicLine", "AtomicCircle", "AtomicArc", "AtomicPolyline", "AtomicNurbsCurve",
    "AtomicEllipse", "AtomicRectangle", "AtomicBox", "AtomicInterpolatedCurve", "AtomicControlPointCurve",
    "AtomicMesh", "AtomicSurface", "AtomicTrimmedSurface", "AtomicCylinder",
    "AtomicBrep", "AtomicTransform",
    "Component", "ComponentResult", "Access", "InputParam", "OutputParam",
    "CURVE", "GEOMETRY", "SURFACE", "CURVE_TYPES", "GEOMETRY_TYPES",
    "CoercionError", "TypeSpec", "accepted_type_names", "coerce_item", "coerce_tree", "type_name",

    # Components
    "Series", "Bounds", "ConstructDomain", "DeconstructDomain",
    "ConstructPoint", "DeconstructPoint", "Distance",
    "UnitX", "UnitY", "UnitZ", "Vector2Pt", "ConstructPlane", "XYPlane", "XZPlane", "YZPlane",
    "CircleCmp", "Ellipse", "LineCmp", "Polygon", "CylinderCmp",
    "CurveMiddle", "Length", "PointOnCurve", "DivideCurve", "DivideDistance", "Interpolate", "TweenCurve", "NurbsCurve", "Polyline", "OffsetCurve",
    "RegionDifference", "RegionIntersection", "RegionUnion",
    "Area", "BoundarySurfaces", "CenterBox", "Cone", "Cylinder", "Extrude", "FourPointSurface", "Loft", "RuledSurface", "Sphere", "Volume",
    "Scale", "ScaleNU", "BoxArray", "CurveArray", "LinearArray", "PolarArray", "RectangularArray",
    "Move", "Orient", "Rotate", "RotateAxis", "Mirror",
    "Characters", "Concatenate", "CullIndex", "ListItem", "ListLength", "PartitionList", "Range", "Random", "ReplaceText", "ReverseList", "ShiftList", "SplitList", "SubList", "TextCase", "TextLength", "TextSplit", "Merge",
    "Boolean", "BoxParam", "BrepParam", "CircleParam", "Curve", "Domain", "Geometry",
    "BooleanToggle", "GraphMapper", "Integer", "LineParam", "MDSlider", "Number", "PlaneParam", "Point", "RectangleParam",
    "SurfaceParam", "Text", "TransformParam", "VectorParam", "NumberSlider", "Panel",
    
    "list_components",
    "CompiledGraph", "GraphCompilerValidationError", "PORT_OP_METHODS",
    "VALID_PORT_OPERATIONS", "compile_graph_document",
    "execute_compiled_graph", "serialize_preview_value",
]
