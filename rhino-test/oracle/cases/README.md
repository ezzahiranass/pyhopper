# Oracle cases

One JSON file per component, `cases/<Tab>/<Class>.json`, written by
`scripts/new_component.py`. Each case names the inputs to feed both pyhopper and the
Grasshopper/RhinoCommon equivalent, the outputs to compare, and a `mode`:

- `exact` — values compared with `tolerance`;
- `structural` — branch paths and item counts only (random components);
- `invariants` — properties listed per case (e.g. containment, unit length).

`"reparametrize": ["curve"]` maps the named curve inputs to the [0, 1] domain on
both sides before comparing parameter-taking outputs (pyhopper curves natively
live on [0, 1]; Rhino's do not). A runner that evaluates these cases through
headless Grasshopper lands with the first oracle-first wave (Vector › Grid).
