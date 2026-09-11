"""Solve real Grasshopper components headlessly (Rhino 8 via Rhino.Inside).

``solve_component`` instantiates a component from the Grasshopper component
server, feeds volatile data straight into its inputs and returns the solved
outputs as ``{output name: {path: [python values]}}``. No canvas, no document
file, no UI: this is how the oracle case files under ``cases/`` are checked
against Grasshopper itself.

Only the value kinds the current waves need are converted (numbers, booleans,
text, intervals, points, vectors, planes, lines); extend ``to_net``/``to_python``
as later waves add geometry.
"""

from __future__ import annotations

from typing import Any

from oracle.support import load, to_arc, to_circle, to_line, to_nurbs_curve, to_nurbs_surface, to_plane, to_point, to_polyline, to_transform, to_vector

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicBox,
    AtomicBrep,
    AtomicCircle,
    AtomicInterval,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
    AtomicSurface,
    AtomicTransform,
    AtomicVector,
)
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path

GRASSHOPPER_PLUGIN_ID = "b45a29b1-4343-4035-989e-044e8580d9cf"
_grasshopper = None
_document = None


def load_grasshopper():
    """Boot Rhino, load the Grasshopper plug-in once and return the ``Grasshopper`` namespace."""
    global _grasshopper, _document
    if _grasshopper is not None:
        return _grasshopper
    load()
    import clr  # type: ignore
    import System  # type: ignore
    from Rhino.PlugIns import PlugIn  # type: ignore

    if not PlugIn.LoadPlugIn(System.Guid(GRASSHOPPER_PLUGIN_ID)):
        raise RuntimeError("Grasshopper plug-in did not load")
    clr.AddReference("Grasshopper")
    import Grasshopper  # type: ignore

    _grasshopper = Grasshopper
    _document = Grasshopper.Kernel.GH_Document()
    return Grasshopper


# ── Reflection helpers (CreateInstance() returns interface-typed proxies under pythonnet) ──


def _params(component):
    return component.GetType().GetProperty("Params").GetValue(component, None)


def _call(component, name: str, *args):
    import System  # type: ignore

    if args:
        types = System.Array[System.Type]([arg.GetType() for arg in args])
        return component.GetType().GetMethod(name, types).Invoke(component, System.Array[System.Object](list(args)))
    return component.GetType().GetMethod(name, System.Array[System.Type]([])).Invoke(component, None)


# ── Value conversion ───────────────────────────────────────────────


def to_net(value: Any, *, reparametrize: bool = False):
    """pyhopper item -> .NET object Grasshopper can wrap as goo (``None`` stays a null).

    Curves become RhinoCommon ``Curve`` objects; with ``reparametrize`` their
    domain is reset to [0, 1] first.
    """
    import System  # type: ignore

    Rhino = load()
    if value is None:
        return None
    if isinstance(value, (AtomicLine, AtomicCircle, AtomicArc, AtomicPolyline, AtomicNurbsCurve)):
        curve = curve_to_rhino(value)
        if reparametrize:
            curve.Domain = Rhino.Geometry.Interval(0.0, 1.0)
        return curve
    if isinstance(value, bool):
        return System.Boolean(value)
    if isinstance(value, int):
        return System.Int32(value)
    if isinstance(value, float):
        return System.Double(value)
    if isinstance(value, str):
        return System.String(value)
    if isinstance(value, AtomicInterval):
        return Rhino.Geometry.Interval(float(value.start), float(value.end))
    if isinstance(value, AtomicPoint):
        return to_point(value)
    if isinstance(value, AtomicVector):
        return to_vector(value)
    if isinstance(value, AtomicPlane):
        return to_plane(value)
    if isinstance(value, AtomicBox):
        half = (float(value.x_size) / 2.0, float(value.y_size) / 2.0, float(value.z_size) / 2.0)
        return Rhino.Geometry.Box(to_plane(value.plane), *(Rhino.Geometry.Interval(-h, h) for h in half))
    if isinstance(value, AtomicSurface):
        return to_nurbs_surface(value)
    if isinstance(value, AtomicBrep):
        if value.face_count != 1 or not isinstance(value.faces[0], AtomicSurface):
            raise TypeError("only single-face untrimmed breps convert to Grasshopper")
        return to_nurbs_surface(value.faces[0])
    if isinstance(value, AtomicTransform):
        return to_transform(value)
    if isinstance(value, AtomicRectangle):
        # pyhopper rectangles are centred on their plane; Rhino's carry corner intervals
        half_x, half_y = float(value.x_size) / 2.0, float(value.y_size) / 2.0
        return Rhino.Geometry.Rectangle3d(to_plane(value.plane), Rhino.Geometry.Interval(-half_x, half_x), Rhino.Geometry.Interval(-half_y, half_y))
    if isinstance(value, Path):
        return _gh_path(value)
    raise TypeError(f"no Grasshopper conversion for {type(value).__name__}")


def to_python(goo: Any):
    """Grasshopper goo -> pyhopper item (``None`` for Grasshopper nulls)."""
    if goo is None:
        return None
    Rhino = load()
    value = goo.ScriptVariable()
    if value is None:
        return None
    if isinstance(value, Rhino.Geometry.Interval):
        return AtomicInterval(float(value.T0), float(value.T1))
    if isinstance(value, Rhino.Geometry.Point3d):
        return AtomicPoint(float(value.X), float(value.Y), float(value.Z))
    if isinstance(value, Rhino.Geometry.Vector3d):
        return AtomicVector(float(value.X), float(value.Y), float(value.Z))
    if isinstance(value, Rhino.Geometry.Plane):
        origin = AtomicPoint(float(value.Origin.X), float(value.Origin.Y), float(value.Origin.Z))
        return AtomicPlane(origin, AtomicVector(float(value.ZAxis.X), float(value.ZAxis.Y), float(value.ZAxis.Z)), AtomicVector(float(value.XAxis.X), float(value.XAxis.Y), float(value.XAxis.Z)))
    if isinstance(value, Rhino.Geometry.Line):
        return AtomicLine(AtomicPoint(float(value.From.X), float(value.From.Y), float(value.From.Z)), AtomicPoint(float(value.To.X), float(value.To.Y), float(value.To.Z)))
    if isinstance(value, Rhino.Geometry.Circle):
        return AtomicCircle(_plane_from_rhino(value.Plane), float(value.Radius))
    if isinstance(value, Rhino.Geometry.Arc):
        return AtomicArc(_plane_from_rhino(value.Plane), float(value.Radius), AtomicInterval(float(value.AngleDomain.T0), float(value.AngleDomain.T1)))
    if isinstance(value, Rhino.Geometry.Polyline):
        return AtomicPolyline(tuple(AtomicPoint(float(pt.X), float(pt.Y), float(pt.Z)) for pt in value))
    if isinstance(value, Rhino.Geometry.Curve):
        return curve_from_rhino(value)
    if isinstance(value, Rhino.Geometry.Box):
        plane = value.Plane
        centre = plane.PointAt(value.X.Mid, value.Y.Mid, value.Z.Mid)
        origin = AtomicPoint(float(centre.X), float(centre.Y), float(centre.Z))
        return AtomicBox(AtomicPlane(origin, AtomicVector(float(plane.ZAxis.X), float(plane.ZAxis.Y), float(plane.ZAxis.Z)), AtomicVector(float(plane.XAxis.X), float(plane.XAxis.Y), float(plane.XAxis.Z))), float(value.X.Length), float(value.Y.Length), float(value.Z.Length))
    if isinstance(value, Rhino.Geometry.Transform):
        return AtomicTransform(tuple(float(getattr(value, f"M{row}{col}")) for row in range(4) for col in range(4)))
    if isinstance(value, Rhino.Geometry.Brep):
        if value.Faces.Count != 1:
            raise TypeError(f"cannot convert a {value.Faces.Count}-face brep to a pyhopper atom")
        return surface_from_rhino(value.Faces[0].ToNurbsSurface())
    if isinstance(value, Rhino.Geometry.Surface):
        return surface_from_rhino(value.ToNurbsSurface())
    if isinstance(value, Rhino.Geometry.Rectangle3d):
        plane = value.Plane
        centre = plane.PointAt(value.X.Mid, value.Y.Mid)
        origin = AtomicPoint(float(centre.X), float(centre.Y), float(centre.Z))
        normal = AtomicVector(float(plane.ZAxis.X), float(plane.ZAxis.Y), float(plane.ZAxis.Z))
        x_axis = AtomicVector(float(plane.XAxis.X), float(plane.XAxis.Y), float(plane.XAxis.Z))
        return AtomicRectangle(AtomicPlane(origin, normal, x_axis), float(value.X.Length), float(value.Y.Length))
    if isinstance(value, (bool, int, float, str)):
        return value
    Grasshopper = load_grasshopper()
    if isinstance(value, Grasshopper.Kernel.Data.GH_Path):
        return _path_from_gh(value)
    type_name = value.GetType().FullName if hasattr(value, "GetType") else type(value).__name__
    raise TypeError(f"no pyhopper conversion for Grasshopper value of type {type_name}")


def curve_to_rhino(value):
    """pyhopper curve atom -> RhinoCommon Curve object (keeps Rhino's native domain)."""
    Rhino = load()
    if isinstance(value, AtomicLine):
        return Rhino.Geometry.LineCurve(to_line(value))
    if isinstance(value, AtomicCircle):
        return Rhino.Geometry.ArcCurve(to_circle(value))
    if isinstance(value, AtomicArc):
        return Rhino.Geometry.ArcCurve(to_arc(value))
    if isinstance(value, AtomicPolyline):
        return Rhino.Geometry.PolylineCurve(to_polyline(value))
    return to_nurbs_curve(value)


def _plane_from_rhino(plane) -> AtomicPlane:
    origin = AtomicPoint(float(plane.Origin.X), float(plane.Origin.Y), float(plane.Origin.Z))
    normal = AtomicVector(float(plane.ZAxis.X), float(plane.ZAxis.Y), float(plane.ZAxis.Z))
    x_axis = AtomicVector(float(plane.XAxis.X), float(plane.XAxis.Y), float(plane.XAxis.Z))
    return AtomicPlane(origin, normal, x_axis)


def curve_from_rhino(curve):
    """RhinoCommon curve -> the most specific pyhopper atom (line, arc/circle, polyline, NURBS)."""
    Rhino = load()
    if isinstance(curve, Rhino.Geometry.LineCurve):
        line = curve.Line
        return AtomicLine(AtomicPoint(float(line.From.X), float(line.From.Y), float(line.From.Z)), AtomicPoint(float(line.To.X), float(line.To.Y), float(line.To.Z)))
    if isinstance(curve, Rhino.Geometry.ArcCurve):
        if curve.IsCompleteCircle:
            return AtomicCircle(_plane_from_rhino(curve.Arc.Plane), float(curve.Radius))
        return to_python_arc(curve.Arc)
    if isinstance(curve, Rhino.Geometry.PolylineCurve):
        return AtomicPolyline(tuple(AtomicPoint(float(curve.Point(i).X), float(curve.Point(i).Y), float(curve.Point(i).Z)) for i in range(curve.PointCount)))
    nurbs = curve if isinstance(curve, Rhino.Geometry.NurbsCurve) else curve.ToNurbsCurve()
    if nurbs is None:
        raise TypeError(f"cannot convert {curve.GetType().FullName} to a pyhopper curve")
    return nurbs_from_rhino(nurbs)


def surface_from_rhino(surface) -> AtomicSurface:
    """RhinoCommon NurbsSurface -> AtomicSurface (poles[v][u], unique knots + multiplicities)."""
    from pyhopper.Utils.Nurbs import collapse_knots, from_rhino_knots

    u_count, v_count = surface.Points.CountU, surface.Points.CountV
    poles = []
    weights = []
    for v in range(v_count):
        row = []
        row_weights = []
        for u in range(u_count):
            control = surface.Points.GetControlPoint(u, v)
            location = control.Location
            row.append(AtomicPoint(float(location.X), float(location.Y), float(location.Z)))
            row_weights.append(float(control.Weight))
        poles.append(tuple(row))
        weights.append(tuple(row_weights))
    u_knots, u_mults = collapse_knots(from_rhino_knots([float(surface.KnotsU[i]) for i in range(surface.KnotsU.Count)]))
    v_knots, v_mults = collapse_knots(from_rhino_knots([float(surface.KnotsV[i]) for i in range(surface.KnotsV.Count)]))
    return AtomicSurface(
        poles=tuple(poles),
        weights=tuple(weights),
        u_knots=tuple(u_knots),
        v_knots=tuple(v_knots),
        u_mults=tuple(u_mults),
        v_mults=tuple(v_mults),
        u_degree=int(surface.Degree(0)),
        v_degree=int(surface.Degree(1)),
    )


def to_python_arc(arc) -> AtomicArc:
    return AtomicArc(_plane_from_rhino(arc.Plane), float(arc.Radius), AtomicInterval(float(arc.AngleDomain.T0), float(arc.AngleDomain.T1)))


def nurbs_from_rhino(nurbs) -> AtomicNurbsCurve:
    from pyhopper.Utils.Nurbs import from_rhino_knots

    points = []
    weights = []
    for i in range(nurbs.Points.Count):
        control = nurbs.Points[i]
        location = control.Location
        points.append(AtomicPoint(float(location.X), float(location.Y), float(location.Z)))
        weights.append(float(control.Weight))
    knots = from_rhino_knots([float(nurbs.Knots[i]) for i in range(nurbs.Knots.Count)])
    return AtomicNurbsCurve(tuple(points), tuple(weights), knots, int(nurbs.Degree))


def output_key(names: list[str], index: int) -> str:
    """Key for output ``index``: the Grasshopper name, suffixed ``#2``, ``#3``... when repeated
    (Length Parameter has two outputs called "Length")."""
    repeat = names[:index].count(names[index])
    return names[index] if repeat == 0 else f"{names[index]}#{repeat + 1}"


def _gh_path(path: Path):
    Grasshopper = load_grasshopper()
    import System  # type: ignore

    indices = list(path) or [0]
    return Grasshopper.Kernel.Data.GH_Path(System.Array[System.Int32]([System.Int32(int(i)) for i in indices]))


def _path_from_gh(gh_path) -> Path:
    return Path(*[int(gh_path[i]) for i in range(gh_path.Length)])


# ── Solving ────────────────────────────────────────────────────────


def solve_component(
    guid: str,
    inputs: dict[int, DataTree],
    *,
    drop_nulls: bool = True,
    reparametrize: tuple[int, ...] = (),
) -> tuple[dict[str, DataTree], list[str]]:
    """Solve one Grasshopper component.

    ``inputs`` maps Grasshopper input indices to DataTrees; inputs that are not
    listed keep Grasshopper's own persistent defaults (or stay empty when the
    port has none). ``reparametrize`` names input indices whose curves are sent
    with a [0, 1] domain — what Grasshopper's "Reparameterize" flag does — so
    parameter outputs compare against pyhopper's native [0, 1] curves.
    Returns ``({output name: DataTree}, runtime messages)``. Grasshopper nulls
    are dropped by default: they are Grasshopper's way of saying "nothing
    here", the analogue of ``Component.NO_OUTPUT``.
    """
    Grasshopper = load_grasshopper()
    import System  # type: ignore

    proxy = Grasshopper.Instances.ComponentServer.EmitObjectProxy(System.Guid(guid))
    if proxy is None:
        raise LookupError(f"Grasshopper has no component {guid}")
    component = proxy.CreateInstance()
    _document.AddObject(component, False)
    try:
        params = _params(component)
        _call(component, "CollectData")  # clears volatile data, keeps persistent defaults, enters the Collected phase
        for index, tree in inputs.items():
            param = params.Input[index]
            param.ClearData()
            for branch_path, branch in tree.branches():
                values = System.Collections.Generic.List[System.Object]()
                for item in branch:
                    values.Add(to_net(item, reparametrize=index in reparametrize))
                param.AddVolatileDataList(_gh_path(branch_path), values)
        _call(component, "ComputeData")

        outputs: dict[str, DataTree] = {}
        names = [param.Name for param in params.Output]
        for index, param in enumerate(params.Output):
            data = param.VolatileData
            branches: dict[Path, list[Any]] = {}
            for gh_path in data.Paths:
                items = [to_python(goo) for goo in data.get_Branch(gh_path)]
                if drop_nulls:
                    items = [item for item in items if item is not None]
                branches[_path_from_gh(gh_path)] = items
            outputs[output_key(names, index)] = DataTree.from_branches(branches)

        messages: list[str] = []
        for level in (Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning, Grasshopper.Kernel.GH_RuntimeMessageLevel.Error):
            messages.extend(str(message) for message in _call(component, "RuntimeMessages", level))
        return outputs, messages
    finally:
        _document.RemoveObject(component, False)
