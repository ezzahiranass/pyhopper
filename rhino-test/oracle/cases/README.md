# Oracle cases

One JSON file per component, `cases/<Tab>/<Class>.json`, written by
`scripts/new_component.py`. Each case names the inputs to feed both pyhopper and the
Grasshopper/RhinoCommon equivalent, the outputs to compare, and a `mode`:

- `exact` — values compared with `tolerance`;
- `structural` — branch paths and item counts only (random components);
- `invariants` — properties listed per case (e.g. containment, unit length).

`"reparametrize": ["curve"]` maps the named curve inputs to the [0, 1] domain on
both sides before comparing parameter-taking outputs (pyhopper curves natively
live on [0, 1]; Rhino's do not). Case files that set it are skipped until the
runner grows curve conversion.

`test_oracle_components.py` is the runner: it solves the real Grasshopper
component headlessly (`gh_headless.py`) with the case inputs and compares the
outputs named in `compare` (Grasshopper port names, matched to pyhopper outputs
by position). Grasshopper nulls are dropped before comparing — they are the
analogue of `Component.NO_OUTPUT`. Inputs a case leaves out keep Grasshopper's
persistent defaults, so cases that exercise a *pyhopper* default need a skip.

Optional knobs:

- fixture `"paths": "simplified"` — compare simplified trees where pyhopper's
  list-output rule (sub-branch only when a branch runs several iterations)
  differs from Grasshopper's unconditional `{path;iteration}`;
- fixture `"notes"` — why a knob is set;
- per case `"gh": {"skip": "reason"}` — a documented deviation; the case still
  runs in pyhopper but is not compared. Record the same reason in the
  component docstring `Notes:`.

`scripts/sync_oracle_cases.py` copies the non-raising golden cases into these
files (inputs and `compare`), preserving the knobs above.
