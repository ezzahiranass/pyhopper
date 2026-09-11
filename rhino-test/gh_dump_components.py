"""
Dump Grasshopper's installed component library (Rhino 8, headless via Rhino.Inside) to JSON.

For every object proxy in the GH ComponentServer: name, nickname, category (tab), subcategory,
exposure, kind, obsolete flag, owning assembly, description, and — for real components —
every input/output param with access mode, type name, optional flag, and description.

Run:  .venv\Scripts\python gh_dump_components.py [output.json]
"""
import json
import sys
import time

OUT = sys.argv[1] if len(sys.argv) > 1 else "gh_components_r8.json"
RHINO_SYSTEM = r"C:\Program Files\Rhino 8\System"

t0 = time.time()
import rhinoinside
rhinoinside.load(RHINO_SYSTEM, "net8.0")
import clr, System
clr.AddReference("RhinoCommon")
import Rhino
core = rhinoinside.get_rhinocore()
print(f"RhinoCore up in {time.time()-t0:.1f}s (v{Rhino.RhinoApp.Version}, headless={Rhino.RhinoApp.IsRunningHeadless})")

from Rhino.PlugIns import PlugIn
gh_id = System.Guid("b45a29b1-4343-4035-989e-044e8580d9cf")
ok = PlugIn.LoadPlugIn(gh_id)
print("LoadPlugIn(Grasshopper) ->", ok)

clr.AddReference("Grasshopper")
import Grasshopper
from Grasshopper.Kernel import GH_Component, GH_ParamAccess

server = Grasshopper.Instances.ComponentServer
proxies = list(server.ObjectProxies)
print("ObjectProxies:", len(proxies))

ACCESS = {int(GH_ParamAccess.item): "item", int(GH_ParamAccess.list): "list", int(GH_ParamAccess.tree): "tree"}


def param_info(p):
    try:
        access = ACCESS.get(int(p.Access), str(p.Access))
    except Exception:
        access = "?"
    return {
        "name": p.Name,
        "nickname": p.NickName,
        "type": p.TypeName,
        "access": access,
        "optional": bool(getattr(p, "Optional", False)),
        "description": p.Description,
    }


records = []
failures = 0
for proxy in proxies:
    desc = proxy.Desc
    rec = {
        "guid": str(proxy.Guid),
        "name": desc.Name,
        "nickname": desc.NickName,
        "category": desc.Category,
        "subcategory": desc.SubCategory,
        "description": desc.Description,
        "exposure": str(proxy.Exposure),
        "kind": str(proxy.Kind),
        "obsolete": bool(proxy.Obsolete),
        "type": proxy.Type.FullName if proxy.Type is not None else None,
    }
    try:
        info = server.FindAssemblyByObject(proxy.Guid)
        rec["assembly"] = info.Name if info is not None else None
        rec["assembly_file"] = System.IO.Path.GetFileName(info.Location) if info is not None and info.Location else None
        rec["is_core"] = bool(info.IsCoreLibrary) if info is not None else None
    except Exception:
        rec["assembly"] = rec["assembly_file"] = None
        rec["is_core"] = None
    try:
        obj = proxy.CreateInstance()
        # CreateInstance() is typed IGH_DocumentObject, so pythonnet only exposes interface members;
        # go through reflection to reach the concrete component's Params server.
        prop = obj.GetType().GetProperty("Params")
        params = prop.GetValue(obj, None) if prop is not None else None
        if params is not None:
            rec["inputs"] = [param_info(p) for p in params.Input]
            rec["outputs"] = [param_info(p) for p in params.Output]
        else:
            rec["inputs"] = rec["outputs"] = None
    except Exception as exc:  # some proxies need UI to instantiate
        failures += 1
        rec["inputs"] = rec["outputs"] = None
        rec["instantiate_error"] = str(exc)[:120]
    records.append(rec)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(records, fh, indent=1, ensure_ascii=False)

print(f"wrote {len(records)} records ({failures} could not be instantiated) -> {OUT} in {time.time()-t0:.1f}s")
core.Dispose()
