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

---

## 3. Respect the inherited solve model

Every normal component should subclass `Component` and let the base class handle:

- input coercion to `DataTree`
- branch and item matching
- access-mode dispatch (`ITEM`, `LIST`, `TREE`)
- path propagation
- output collection
- `ComponentResult` wrapping

That means:

- declare `inputs`
- declare `outputs`
- implement `generate()`

Do not reimplement the solve pipeline in each component.
Only override `__new__` or bypass the standard pipeline when the component
truly requires special tree-level behavior, as in `Merge`.

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

Rules of thumb:

- `ITEM` for per-item transforms and analysis
- `LIST` when a whole branch must be seen together
- `TREE` only when the component truly needs whole-tree awareness

Examples:

- `Polygon` should use `LIST`
- `Merge` is effectively tree-level
- most transforms like `Move` and `Rotate` use `ITEM`

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

## 7. Keep `generate()` stateless and side-effect-free

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

## 8. Use the core data model instead of ad-hoc objects

When a component works with geometry or structured values:

- use atoms from `pyhopper.Core.Atoms`
- preserve the existing atom naming conventions
- use adapters from `pyhopper.Utils.Adapters` for geometry backend operations

Do not invent per-component geometry containers or special output shapes when
an existing atom already represents the concept.

---

## 9. Frontend metadata must stay declarative

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

## 10. Match top-level exports deliberately

If the component should be available from `import pyhopper as ph`, add it to:

- `pyhopper/__init__.py`

If it only belongs in module-level imports, keep it local to its package.

Do not export experimental or incomplete components from the top level unless
you want them treated as public API.

---

## 11. Sanity-check every new component

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

---

## 12. A good example to copy

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
