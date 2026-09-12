"""
Test 1: Boot Rhino 8 HEADLESS inside this CPython process (Rhino.Inside) and do geometry.
No GUI window is shown. Run with: .venv\Scripts\python test1_headless_rhino.py
"""
import os, sys, time

RHINO_SYSTEM = r"C:\Program Files\Rhino 8\System"
FRAMEWORK = sys.argv[1] if len(sys.argv) > 1 else "net48"

t0 = time.time()
import rhinoinside
# Official loader: picks the matching Rhino.Inside resolver DLL and boots RhinoCore hidden.
# Try Rhino 8 hosted on .NET Framework 4.8 first (what Revit-style hosts use).
rhinoinside.load(RHINO_SYSTEM, FRAMEWORK)
import clr, System
clr.AddReference("RhinoCommon")
import Rhino
core = rhinoinside.get_rhinocore()
print(f"RhinoCore up in {time.time()-t0:.1f}s via rhinoinside ({FRAMEWORK})")
print("RhinoCommon assembly :", Rhino.RhinoApp.Version if hasattr(Rhino.RhinoApp, "Version") else "?")
print("Rhino version         :", Rhino.RhinoApp.Version)
print("Build date            :", Rhino.RhinoApp.BuildDate)
print("Is running headless   :", Rhino.RhinoApp.IsRunningHeadless)
print("Main window handle    :", Rhino.RhinoApp.MainWindowHandle().ToInt64())
print("Active doc            :", Rhino.RhinoDoc.ActiveDoc)

# ---- Geometry work, no document needed --------------------------------------
from Rhino.Geometry import Sphere, Point3d, Brep, Mesh, MeshingParameters, Box, Plane, Interval
sph = Sphere(Point3d(0, 0, 0), 5.0)
brep = sph.ToBrep()
print("Sphere brep faces     :", brep.Faces.Count, " valid:", brep.IsValid)
mp = Rhino.Geometry.VolumeMassProperties.Compute(brep)
print("Volume (exact 523.6)  :", round(mp.Volume, 3))
meshes = Mesh.CreateFromBrep(brep, MeshingParameters.Default)
m = Mesh(); [m.Append(x) for x in meshes]
print("Mesh verts/faces      :", m.Vertices.Count, "/", m.Faces.Count)

# Boolean: sphere minus box (needs the full SDK, not rhino3dm)
box = Box(Plane.WorldXY, Interval(0, 10), Interval(0, 10), Interval(0, 10)).ToBrep()
diff = Brep.CreateBooleanDifference(brep, box, 0.001)
print("Boolean diff result   :", None if diff is None else f"{len(diff)} brep(s), faces={diff[0].Faces.Count}")

# ---- Document work (headless doc) --------------------------------------------
doc = Rhino.RhinoDoc.CreateHeadless(None)
oid = doc.Objects.AddBrep(brep)
print("Headless doc objects  :", doc.Objects.Count, " added id:", oid)

# ---- Try running a Rhino command by name (works headless?) -------------------
ok = Rhino.RhinoApp.RunScript("_-Circle 0,0,0 3 _Enter", False)
print("RunScript _Circle     :", ok, " (ActiveDoc objects:",
      None if Rhino.RhinoDoc.ActiveDoc is None else Rhino.RhinoDoc.ActiveDoc.Objects.Count, ")")

core.Dispose()
print("Shut down cleanly. Total", f"{time.time()-t0:.1f}s")
