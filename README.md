# pyhopper

Declarative parametric 3D modeling in Python — a Grasshopper-inspired framework: immutable geometric
atoms, DataTree data flow, 450+ components that mirror Grasshopper 8's core library, a graph compiler
that turns a node document into Python and a GLB, and a Rhino 8 oracle that checks the components
against Grasshopper itself. The documentation lives in [`docs/`](docs/index.md) (mkdocs).

## Layout

| Path | What lives there |
| --- | --- |
| `pyhopper/` | The package: `Core` (atoms, DataTree, Component), `Components/<Tab>/<Category>/`, `Utils/` (NURBS, curves, surfaces, intersections, exporters), `Graph/` (document compiler and runtime). |
| `tests/` | unittest suite with the golden fixtures (`tests/golden/`) that pin every component's Grasshopper-verified behaviour. |
| `rhino-test/` | The headless Rhino 8 / Grasshopper oracle (`rhino-test/oracle`), the component dump and the scaffolding helpers (`gh_defaults.py`, `gh_probe.py`). Needs a local Rhino 8. |
| `docs/`, `mkdocs.yml` | Site sources; reference pages are generated from the package docstrings. |
| `scripts/` | `check.sh` / `check.ps1` (whole-repo check), `new_component.py` (scaffold from the Grasshopper dump), `sync_oracle_cases.py`. |
| `CONTRACTS/` | Design contracts for atoms, curves/surfaces and new components. |

## Develop

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e . shapely mkdocs-material mkdocstrings[python] mkdocs-gen-files mkdocs-literate-nav
.venv/Scripts/python -m unittest discover -s tests -t .              # the suite (~640 tests)
DISABLE_MKDOCS_2_WARNING=true .venv/Scripts/python -m mkdocs serve -a 127.0.0.1:8001
RHINO_ORACLE=1 scripts/check.sh                                      # + the Grasshopper oracle (Rhino 8 required)
```

`shapely` is optional at runtime (region booleans); everything else is the standard library.

## Versioning

Products consume this repo as a `git subtree` pinned to release tags (`vX.Y.Z`). The version is
`pyproject.toml` / `pyhopper.__version__`; bump both in the release commit, then tag.
