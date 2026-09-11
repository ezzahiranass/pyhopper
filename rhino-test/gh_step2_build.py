# Runs inside Rhino 7 through inside_bridge.py. Builds a small GH definition on a live canvas.
import clr, System, time
import Rhino
clr.AddReference("Grasshopper")
clr.AddReference("GH_IO")
import Grasshopper
from Grasshopper.Kernel import GH_Document, GH_DocumentIO
from System.Drawing import PointF

gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
if not gh.IsEditorLoaded():
    gh.LoadEditor()
gh.ShowEditor()
print("editor loaded:", gh.IsEditorLoaded())

server = Grasshopper.Instances.ComponentServer
print("component proxies available:", server.ObjectProxies.Count)

def find(name, category=None, subcat=None):
    """Find a component proxy by exact Name (+ optional Category/SubCategory) and instantiate it."""
    hits = [p for p in server.ObjectProxies
            if p.Desc.Name == name and not p.Obsolete
            and (category is None or p.Desc.Category == category)
            and (subcat is None or p.Desc.SubCategory == subcat)]
    if not hits:
        raise Exception("no component named %r" % name)
    return hits[0].CreateInstance()

def add(obj, x, y, nick=None):
    obj.CreateAttributes()
    obj.Attributes.Pivot = PointF(x, y)
    if nick:
        obj.NickName = nick
    doc.AddObject(obj, False)
    return obj

# --- fresh document on the canvas -------------------------------------------
doc = GH_Document()
Grasshopper.Instances.DocumentServer.AddDocument(doc)
Grasshopper.Instances.ActiveCanvas.Document = doc
doc.Enabled = True

# --- nodes -------------------------------------------------------------------
radius = add(find("Number Slider"), 40, 60, "radius")
radius.Slider.Minimum = System.Decimal(1)
radius.Slider.Maximum = System.Decimal(50)
radius.Slider.Value   = System.Decimal(12.5)

height = add(find("Number Slider"), 40, 140, "height")
height.Slider.Minimum = System.Decimal(1)
height.Slider.Maximum = System.Decimal(100)
height.Slider.Value   = System.Decimal(30)

circle  = add(find("Circle", "Curve", "Primitive"), 280, 60)
unitz   = add(find("Unit Z", "Vector", "Vector"), 280, 160)
extrude = add(find("Extrude", "Surface", "Freeform"), 480, 100)
volume  = add(find("Volume", "Surface", "Analysis"), 680, 100)
panel   = add(find("Panel", "Params", "Input"), 880, 100, "result")

# --- wires -------------------------------------------------------------------
circle.Params.Input[1].AddSource(radius)                    # Circle.R  <- slider
unitz.Params.Input[0].AddSource(height)                     # UnitZ.F   <- slider
extrude.Params.Input[0].AddSource(circle.Params.Output[0])  # Extrude.B <- Circle.C
extrude.Params.Input[1].AddSource(unitz.Params.Output[0])   # Extrude.D <- UnitZ.V
volume.Params.Input[0].AddSource(extrude.Params.Output[0])  # Volume.G  <- Extrude.E
panel.AddSource(volume.Params.Output[0])                    # Panel     <- Volume.V

# --- solve & read back -------------------------------------------------------
t0 = time.time()
doc.NewSolution(True)
print("solved in %.2fs, objects on canvas: %d" % (time.time()-t0, doc.ObjectCount))
vol = [g.Value for g in volume.Params.Output[0].VolatileData.AllData(True)]
import math
print("Volume from GH   :", vol, "| expected pi*12.5^2*30 =", round(math.pi*12.5**2*30, 3))
print("Extrude out type :", extrude.Params.Output[0].VolatileData.get_Branch(0)[0].TypeName)
print("Panel shows      :", [str(g) for g in panel.VolatileData.AllData(True)])
print("Errors on canvas :", [ (o.NickName, list(o.RuntimeMessages(Grasshopper.Kernel.GH_RuntimeMessageLevel.Error))) for o in doc.Objects if o.RuntimeMessageLevel == Grasshopper.Kernel.GH_RuntimeMessageLevel.Error])

canvas = Grasshopper.Instances.ActiveCanvas
canvas.Viewport.ZoomExtents(doc.BoundingBox(False), True) if hasattr(canvas.Viewport, "ZoomExtents") else None
canvas.Refresh()
NS_KEEP = dict(doc=doc, radius=radius, height=height, circle=circle, unitz=unitz, extrude=extrude, volume=volume, panel=panel)
globals().update(NS_KEEP)
