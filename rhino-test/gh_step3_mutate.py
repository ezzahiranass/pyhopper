import math, time
from System.Drawing import PointF
import Grasshopper
# 1) INSERT a node between Extrude and Volume: Cap Holes, and REWIRE
cap = add(find("Cap Holes", "Surface", "Util"), 600, 100)
volume.Params.Input[0].RemoveAllSources()
cap.Params.Input[0].AddSource(extrude.Params.Output[0])
volume.Params.Input[0].AddSource(cap.Params.Output[0])
# 2) RENAME nodes
circle.NickName = "base circle"
extrude.NickName = "extrude up"
# 3) UPDATE a value
radius.Slider.Value = System.Decimal(10)
radius.ExpireSolution(True)
# 4) DELETE a node
doc.RemoveObject(panel, True)
# 5) MOVE a node
volume.Attributes.Pivot = PointF(800, 100)
volume.Attributes.ExpireLayout()
doc.NewSolution(True)
vol = [g.Value for g in volume.Params.Output[0].VolatileData.AllData(True)]
print("closed?      :", [g.Value.IsSolid for g in cap.Params.Output[0].VolatileData.AllData(True)])
print("Volume now   :", [round(v, 3) for v in vol], "| expected pi*10^2*30 =", round(math.pi*100*30, 3))
print("nodes on canvas:", [(o.NickName, o.Name) for o in doc.Objects])
print("wires        :", [(s.Attributes.GetTopLevel.DocObject.NickName + " -> " + o.NickName) for o in doc.Objects if hasattr(o, "Params") for p in o.Params.Input for s in p.Sources] + [(s.Attributes.GetTopLevel.DocObject.NickName + " -> " + o.NickName) for o in doc.Objects if not hasattr(o, "Params") and hasattr(o, "Sources") for s in o.Sources])
canvas = Grasshopper.Instances.ActiveCanvas
canvas.Viewport.ZoomExtents(doc.BoundingBox(False), True)
canvas.Refresh()
