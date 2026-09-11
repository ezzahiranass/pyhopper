# rhino-test — what Claude can do with Rhino/Grasshopper on this machine (tested 2026-09-10)

| Capability | Rhino 7.3 (`C:\Program Files\Rhino 7`) | Rhino 8.35 (`C:\Program Files\Rhino 8`) |
|---|---|---|
| Headless, in-process from CPython (Rhino.Inside, no window) | not tested | **works** — `test1_headless_rhino.py net8.0` (boots in ~3s: breps, booleans, meshing, headless docs) |
| Drive the GUI from outside (COM `Rhino.Application.N` → `RunScript`) | works (plain commands) | works (plain commands) — `rhino_bridge.py` + `rh.py` |
| Run Python *inside* the GUI instance | works (IronPython 2.7) | works (CPython 3.9) |
| Grasshopper: add / wire / insert / rename / update / delete / move nodes, solve, read outputs | GH plugin loads (editor not verified — instance got closed) | **works** — `gh_step2_build.py`, `gh_step3_mutate.py`, see `gh_canvas_result.png` |

Caveat: when Rhino 8 runs in the "license does not allow saving" mode, it also disables the script-runner
commands (`RunPythonScript`, `EditPythonScript`, `RunScript`) and Rhino.Inside fails to boot (`E_FAIL`);
only plain commands through COM worked in that state.

## How to use
```
.venv\Scripts\python test1_headless_rhino.py net8.0            # headless Rhino 8
"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="_-RunPythonScript D:\Apps\pyhopper\rhino-test\inside_bridge.py"
.venv\Scripts\python px.py -c "import Rhino; print(Rhino.RhinoApp.Version)"   # exec code inside the running Rhino
.venv\Scripts\python px.py gh_step2_build.py                    # build a GH definition on the live canvas
```
`tools/` holds window capture / close / show helpers (PrintWindow-based, no focus stealing).

## Grasshopper library dump (2026-09-11)
`gh_dump_components.py` boots Rhino 8 headless, loads the Grasshopper plug-in and serialises every
`ComponentServer` proxy (name, nickname, tab, subcategory, exposure, obsolete flag, owning assembly and
every input/output with its `GH_ParamAccess`). Note: `proxy.CreateInstance()` comes back interface-typed
under pythonnet, so `Params` is reached through `GetType().GetProperty("Params")`.

- `gh_core_components_r8.json` — the 799 visible, non-obsolete core components (Kangaroo/LunchBox/
  Galapagos/script assemblies and the Rhino-document tab excluded). Use it as the port contract when
  adding a component (NEW_COMPONENT.md: verify Grasshopper first).
- `component_roadmap_plan.json` — those 799 joined with pyhopper's catalog: 117 covered, 679 candidates
  tiered (T1 safe now / T2 one infra item / T3 later / T4 not now) with batch and dependency tags.
