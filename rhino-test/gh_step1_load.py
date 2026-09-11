import Rhino, System, time
from Rhino.PlugIns import PlugIn
gh_id = System.Guid("b45a29b1-4343-4035-989e-044e8580d9cf")
print("installed:", len(PlugIn.GetInstalledPlugInNames()), "| GH path:", PlugIn.PathFromId(gh_id))
t0 = time.time()
ok = PlugIn.LoadPlugIn(gh_id)
print("LoadPlugIn(Grasshopper) ->", ok, "in %.1fs" % (time.time()-t0))
print("GH plugin loaded:", PlugIn.PlugInExists(gh_id, System.Boolean(False), System.Boolean(False)) if False else PlugIn.Find(gh_id) is not None)
gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
print("GH scripting object:", gh)
print("IsEditorLoaded:", gh.IsEditorLoaded())
