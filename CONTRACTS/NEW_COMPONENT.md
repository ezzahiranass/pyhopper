# Adding a New Component

This project only stays coherent if new components respect the existing
`Component` inheritance model, the DataTree solve pipeline, and the way the
MkDocs reference site is generated.

Use this document as the checklist for any new component.

Before implementing a component, verify how the matching Grasshopper component
actually behaves.

Rule:

- Search the web first, preferably Grasshopper Docs, Rhino/Grasshopper API docs,
  or McNeel sources.
- Confirm the component's tab/category, inputs, outputs, and behavior before
  writing code.
- Do not invent ports, names, or semantics from memory when the Grasshopper
  behavior can be checked.

---

## 1. Choose the right Grasshopper location first

The module path under `pyhopper/Components/` is not cosmetic.

- The first folder under `Components/` becomes the **tab** in the frontend catalog.
- The next folder(s) become the **category**.
- The filename becomes the reference page slug in MkDocs.

Examples:

- `pyhopper/Components/Curve/Primitive/Circle.py`
  Maps to tab `Curve`, category `Primitive`, component `Circle`
- `pyhopper/Components/Params/Input/NumberSlider.py`
  Maps to tab `Params`, category `Input`, component `NumberSlider`

Rule:

- Place the component where a Grasshopper user would expect to find it.
- Do not create ad-hoc tabs or categories when an established Grasshopper
  location already exists.

---

## 2. Keep the component class clean

Component classes should use the clean user-facing name:

- `Circle`
- `Move`
- `DivideCurve`
- `NumberSlider`

Do not add suffixes like `CircleComponent` to avoid collisions with atoms.
If there is a naming conflict with the core data model, the atom should carry the
disambiguation instead, for example `AtomicCircle`, `AtomicLine`, `AtomicPoint`.

Class and port names are *derived* from the Grasshopper names by
`pyhopper/Graph/naming.py` (`class_name_for`, `port_name_for`) and checked by
`tests/test_component_naming.py` / `tests/test_component_metadata.py`:
`Line | Line` → `LineLine`, `Line + Pt` → `LinePlusPt`, `Tangent Lines (Ex)` →
`TangentLinesEx`, `Rectangle 2Pt` → `Rectangle2Pt`, `Pick'n'Choose` →
`PickNChoose`; ports become snake_case (`X coordinate` → `x_coordinate`,
`Values A` → `values`, numbered `Stream N` ports collapse into one variadic
`streams`). Exceptions go into the override tables in that module, never into
ad-hoc names. Class names must be unique across all tabs except `Params`.

---

## 3. Respect the inherited solve model

Every component subclasses `Component` and lets the base class handle:

- input binding and coercion to `DataTree`
- branch pairing across inputs and per-input access (`ITEM`, `LIST`, `TREE`)
- path propagation and output collection
- `ComponentResult` wrapping

That means:

- declare `inputs` (each with the access Grasshopper gives that port)
- declare `outputs`
- implement `generate()`

Never override `__new__` and never reimplement iteration inside `generate()`.
The pipeline follows Grasshopper's rules exactly:

| Declared access | Drives iteration? | `generate()` receives |
|---|---|---|
| `ITEM` | yes — iterated item by item inside the branch (longest list, last item repeated) | one item |
| `LIST` | yes — one call per branch | the whole branch as a `list` |
| `TREE` | no — supplied whole to every call | the `DataTree` |
| optional input, absent or empty branch | — | the keyword is omitted (the signature default applies) |
| variadic tail (`variadic_inputs = True`) | each stream is a pseudo-input with the declared access | `name=[stream, stream, ...]` |

Branch pairing: the *principal* tree (most branches, then deepest path) drives
iteration; other iterated inputs contribute the branch at the same path or, when
missing, their last branch. Inside a branch the number of calls is the longest
`ITEM` branch; a required `ITEM` input with an empty branch makes zero calls and
the output branch stays empty. Empty or silent branches are preserved as empty
output branches (Grasshopper keeps topology).

Inside `generate()` you can use:

- `self.iteration` — an `IterationContext(path, index, count)` for the current call
- `Component.NO_OUTPUT` — return it (or use it as one element of the output
  tuple) to emit nothing for this call
- `self.sub_branches(lists)` — build a `DataTree` with one branch per list under
  the current branch (`{path;k}`, or `{path;index;k}` when the branch runs
  several item iterations); return it to place chunks explicitly

Calling a component with extra positional arguments or unknown keywords raises
`TypeError`; a required input that is neither connected nor defaulted raises too.

Variadic inputs (`Merge`, `Entwine`, `Weave`, `Sort List` values…) set
`variadic_inputs = True` on the class; the *last* declared input then accepts
any number of streams. `Merge(a, b)` and `Merge(data=[a, b])` are equivalent.

---

## 4. Write the module in the standard shape

Use this structure:

```python
"""ComponentName - One-line module summary."""

from pyhopper.Core.Component import Component, InputParam, OutputParam, Access


class ComponentName(Component):
    """One-line class summary.

    Optional extra detail that explains what the component accepts, what it
    returns, and any important access-mode or branching behavior.
    """

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("geometry")]

    def generate(self, geometry=None, factor=1.0):
        return ...
```

Guidelines:

- Add a **module docstring** as the first line of the file.
- Add a **class docstring** on the component class.
- Keep `generate()` small and focused.
- Use explicit defaults in both `InputParam(...)` and the `generate(...)` signature.

---

## 5. Follow the MkDocs docstring style

`mkdocs.yml` configures `mkdocstrings` with:

- `docstring_style: google`

So docstrings should be plain, readable, and compatible with Google-style
sections when needed.

For most components, the minimum good standard is:

- a one-line summary
- one short paragraph describing accepted inputs and produced outputs
- any important note about access mode, branch behavior, or special semantics

Example:

```python
class DivideCurve(Component):
    """Divide a curve into evenly spaced ``Point3d`` samples.

    Accepts a ``Circle``, ``Arc``, ``Polyline``, or ``NurbsCurve`` and returns
    ``count`` points in a single output branch per input curve.
    """
```

Use extra Google-style sections only when they add clarity.
Do not write empty `Args:` or `Returns:` sections just because the style supports them.

---

## 6. Declare inputs and outputs precisely

Inputs and outputs are part of the framework contract, not just UI metadata.

When defining them:

- use `InputParam(name, type_hint, access, default=..., optional=...)`
- use `OutputParam(name, type_hint)` when you know the output type
- choose `Access.ITEM`, `Access.LIST`, or `Access.TREE` intentionally
- treat every non-`None` `type_hint` as an enforced runtime contract. The
  central type system coerces every incoming tree item before `generate()`
  while preserving paths and item counts.
- declare plane inputs with the precise `AtomicPlane` type. The framework
  automatically coerces an incoming `AtomicPoint` into a World-XY plane
  centered at that point for ITEM, LIST, and TREE access.

Rules of thumb:

- copy the access Grasshopper declares for the matching port (the dump in
  `rhino-test/gh_core_components_r8.json` lists it as `[item]`, `[list]`, `[tree]`)
- `ITEM` for per-item transforms and analysis
- `LIST` when a whole branch must be seen together (the list ports of
  `List Item`, `Partition List`, `Polyline` vertices)
- `TREE` only for whole-tree operations (`Merge`, `Flatten Tree`, `Graft Tree`)

Mixed access is the normal case, not the exception: `List Item` declares
`list` as `LIST` and `index`/`wrap` as `ITEM`, so three indices in one branch
produce three items in that branch — no `__new__` override, no `[0]` reducer.

Also declare the Grasshopper identity on the class so the catalog can show it
and the metadata test can check the port contract:

```python
display_name = "List Item"      # exact Grasshopper name
nickname = "Item"               # Grasshopper nickname
gh_guid = "59daf374-bc21-4a5e-8282-5504fb7ae9ae"
gh_extra_inputs = ()            # names of pyhopper-only trailing inputs, if any
```

### Never use `default=None` as a stand-in for a real default value

If an input has a natural fallback (e.g. a plane that defaults to world XY, a
domain that defaults to `[0, 1]`), set that real value directly in both
`InputParam` and the `generate()` signature. Do not use `None` as a placeholder
and then guard for it inside `generate()`.

Do:

```python
InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),

def generate(self, plane=AtomicPlane.world_xy()):
    ...
```

Do not change a plane input's type hint to `None` merely to accept points.
Point-to-plane conversion is a framework-level Grasshopper-compatible coercion,
so future plane-based components inherit it automatically.

Other deterministic one-to-one conversions, primitive normalization, semantic
Curve/Geometry acceptance, and structured coercion failures belong in
`Core/TypeSystem.py`. Components and parameter containers must not duplicate
those rules locally. Ambiguous or one-to-many extraction, such as converting a
multi-face Brep to a Surface or a Surface to boundary Curves, requires an
explicit extraction component and must not be added as a coercion.

Do not:

```python
InputParam("plane", AtomicPlane, Access.ITEM, default=None, optional=True),

def generate(self, plane=None):
    if plane is None:
        plane = AtomicPlane.world_xy()  # <-- bad
```

The only legitimate use of `default=None` is when `None` is a genuine sentinel
that changes the component's behavior — for example, an optional projection
plane where the absence of a plane means "skip the projection step entirely".
In that case, keep `optional=True` as well so the pipeline does not raise when
the input is missing.

---

## 7. Understand how return types affect output branching

What `generate()` returns determines the output tree structure:

- **Scalar / atom** → one item appended to the current branch.
  Example: `Addition` returns a `float`. Input `{0}[1,2,3]` + `{0}[10,20,30]`
  produces `{0}[11, 22, 33]` — same branch, one output per input item.

- **List** → items go into a sub-branch when multiple inputs are iterated.
  Example: `Series` returns `[0.0, 1.0, ...]`. If the `count` input is
  `{0}[3, 5]` (two items), the output is:
  ```
  {0;0} [0, 1, 2]        ← from count=3
  {0;1} [0, 1, 2, 3, 4]  ← from count=5
  ```
  Each invocation's list gets its own sub-branch at `path;item_index`.
  If only one item is iterated (e.g. `count` is a single `5`), the list
  goes directly into the current branch `{0}[0, 1, 2, 3, 4]` — no
  extra nesting.

This matches Grasshopper's behavior where `DA.SetDataList` auto-branches
when there are multiple iterations per branch. When writing a new
component, decide: does each invocation produce **one value** or
**a collection of values**? Return a scalar for the former, a list for
the latter. The framework handles the branching.

For **multi-output** components returning a tuple, each element is handled
independently — some outputs can be scalars and others lists.

- **`Component.NO_OUTPUT`** → nothing is emitted for this call. Use it for
  events that have no result (parallel lines in `Line | Line`, an
  out-of-range index without wrap). The branch is still kept, empty, when no
  call of the branch emitted anything.

- **`DataTree`** → merged by absolute path. Build it with
  `self.sub_branches(lists)` when the component partitions its input
  (`Partition List` writes chunk `k` to `{path;k}`), or construct it directly
  for whole-tree operations (`Merge`, `Flatten Tree`).

---

## 8. Keep `generate()` stateless and side-effect-free

`generate()` should compute an output from matched inputs only.

Do:

- convert types explicitly when needed
- call adapters/utilities
- return a single value or a tuple matching `outputs`

Do not:

- mutate global state
- perform UI work
- bypass DataTree matching
- rely on hidden state between calls

This rule is what preserves the framework's consistency across item, list,
and tree execution.

---

## 9. Use the core data model instead of ad-hoc objects

When a component works with geometry or structured values:

- use atoms from `pyhopper.Core.Atoms`
- preserve the existing atom naming conventions
- use adapters from `pyhopper.Utils.Adapters` for geometry backend operations

Do not invent per-component geometry containers or special output shapes when
an existing atom already represents the concept.

---

## 10. Frontend metadata must stay declarative

Some components may need frontend-specific rendering hints.

That is acceptable only if:

- the component still behaves as a normal `Component`
- the solve model remains intact
- frontend metadata is declarative and optional

Example:

- `NumberSlider` is still a zero-input component with one `value` output
- the web frontend may read `frontend_preset` and `frontend_config`
- the component itself does not become a UI object

Frontend metadata must never replace:

- `inputs`
- `outputs`
- `generate()`
- the inherited DataTree pipeline

---

## 11. Match top-level exports deliberately

If the component should be available from `import pyhopper as ph`, add it to:

- `pyhopper/__init__.py`

If it only belongs in module-level imports, keep it local to its package.

Do not export experimental or incomplete components from the top level unless
you want them treated as public API.

---

## 12. Sanity-check every new component

Before considering a component done, verify:

- the tab/category path is correct
- module and class docstrings are present
- `inputs` and `outputs` are declared correctly
- `generate()` is stateless
- the component relies on the inherited solve pipeline
- output names and types are sensible
- top-level exports are intentional
- auto-generated docs will read cleanly

If the component appears in the frontend catalog, also verify:

- the metadata reported by `list_components()` is correct
- any frontend preset remains declarative

For components with a `gh_guid`, also run the Grasshopper oracle when Rhino 8 is
available: `scripts/sync_oracle_cases.py` mirrors the golden cases into
`rhino-test/oracle/cases/`, and `RHINO_ORACLE=1 scripts/check.sh` solves the real
Grasshopper component headlessly with the same inputs. Every case that legitimately
differs gets `"gh": {"skip": "reason"}` in the case file **and** the same reason in
the docstring `Notes:` — the case file documents the deviation, the docstring
explains it to users.

---

## 13. A good example to copy

`NumberSlider` is a good pattern for a parameter-style component:

- correct Grasshopper location: `Params/Input`
- clean component name
- standard zero-input `Component`
- one output named `value`
- declarative frontend metadata only
- no custom solve behavior

When in doubt, prefer copying the shape of existing components like:

- `Circle`
- `DivideCurve`
- `Series`
- `UnitZ`

and only introduce exceptions when the framework genuinely requires them.
