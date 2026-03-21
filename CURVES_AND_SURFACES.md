# Curves and Surfaces in pyhopper

This document explains how pyhopper represents, converts, tessellates, and
will eventually process curves and surfaces. It is written for contributors
who may not have a NURBS or CAD background, and it doubles as the binding
contract for every future component that touches curve or surface geometry.

Read this before writing any component under `Components/Curve/`,
`Components/Surface/`, or any adapter/unifier that touches geometry.

---

## 1. The Atom Layer — What Curves and Surfaces Actually Are

Every piece of geometry in pyhopper is an **Atom**: a frozen, immutable
dataclass that carries pure data and no behavior. Atoms flow through
DataTrees. Components read atoms, compute, and produce new atoms. Nothing
mutates.

### 1.1 Curve Atoms

| Atom | What it stores | Typical origin |
|---|---|---|
| `AtomicLine` | two endpoints | `Line`, `LineSDL` components |
| `AtomicPolyline` | ordered tuple of points | `Polygon`, `Rectangle` |
| `AtomicCircle` | plane + radius | `Circle`, `CircleCNR`, `Circle3Pt` |
| `AtomicArc` | plane + radius + angle interval | arc components |
| `AtomicNurbsCurve` | control points, weights, knots, degree | spline components, unification |

The first four are **named-shape atoms** — their geometry is fully defined by
a few human-readable fields (center, radius, start, end, etc.). They are
cheap to create, easy to inspect, and map directly to the Grasshopper types
users expect.

`AtomicNurbsCurve` is the **general representation**. Any of the named shapes
above can be converted into a NURBS curve without loss. The reverse is not
true — an arbitrary NURBS curve cannot always be reduced to a circle or a
line. This asymmetry drives the entire conversion pipeline.

### 1.2 The Surface Atom

There is one surface atom: **`AtomicSurface`**.

```
AtomicSurface
├── poles          2D grid of AtomicPoint  (rows × columns)
├── weights        2D grid of float        (same shape as poles)
├── u_knots        tuple of unique knot values in U
├── v_knots        tuple of unique knot values in V
├── u_mults        multiplicity of each U knot
├── v_mults        multiplicity of each V knot
├── u_degree       polynomial degree in U
├── v_degree       polynomial degree in V
├── u_periodic     bool
└── v_periodic     bool
```

This is an **OCCT-style tensor-product B-spline surface** — the same
representation used by Open CASCADE, Rhino, and most BREP kernels. The
key concept: a point on the surface is computed by evaluating two
independent B-spline basis functions (one in U, one in V) and combining
them over the control-point grid.

There is also `AtomicMesh` (vertices + face index tuples) for polygonal
output, but meshes are a display/export artifact — the authoritative
geometry lives in `AtomicSurface`.

---

## 2. NURBS Primer — Degrees, Knots, Spans, and Weights

If you already know NURBS, skip to section 3. If not, this section gives
you the minimum vocabulary needed to work on pyhopper geometry.

### 2.1 What is a B-Spline?

A B-spline curve is a smooth curve defined by:

- **Control points** — a sequence of points that influence the curve's
  shape. The curve generally does not pass through these points (except at
  the endpoints of a clamped spline).
- **Degree** — the polynomial degree of each piece of the curve.
  - Degree 1: piecewise linear (straight segments between control points).
  - Degree 2: piecewise quadratic (can exactly represent circles and arcs).
  - Degree 3: piecewise cubic (the most common smooth spline).
- **Knot vector** — a non-decreasing sequence of parameter values that
  determines where one polynomial piece ends and the next begins.

### 2.2 Knots and Spans

The **knot vector** partitions the parameter space into **spans**. Each span
is the interval between two consecutive *distinct* knot values. Within a
single span the curve is a single polynomial of the declared degree.

Example for a degree-2 curve with 9 control points (a full NURBS circle):

```
Unique knots:       0.00    0.25    0.50    0.75    1.00
Multiplicities:       3       2       2       2       3
Full knot vector:   [0, 0, 0,  0.25, 0.25,  0.50, 0.50,  0.75, 0.75,  1, 1, 1]
                     └─span 1─┘└──span 2──┘└──span 3──┘└──span 4──┘
```

Four spans, each covering a quarter of the circle (90°).

**Multiplicity** is how many times a knot value appears in the full vector.
Higher multiplicity reduces smoothness at that knot:

- Multiplicity 1: the curve is smooth (C^(degree-1) continuous).
- Multiplicity = degree: the curve is only positionally continuous (a
  "corner" or tangent break).
- Multiplicity = degree + 1 (at the ends): the curve is **clamped** — it
  starts and ends exactly at the first and last control points.

Pyhopper stores knots in **unique + multiplicity** form (matching the OCCT
convention) rather than as a flat repeated vector. The helper
`_expand_knots(knots, mults)` converts between the two when needed.

### 2.3 Weights (Rational Splines)

When every weight is 1.0, the curve is a plain B-spline. When weights vary,
it becomes a **NURBS** (Non-Uniform Rational B-Spline). Weights let the
curve represent conic sections exactly:

- A circle uses weights of `1.0` at on-curve points and `cos(half_span)`
  at off-curve midpoints.
- Changing a weight pulls the curve toward or away from that control point.

In `AtomicSurface`, weights form a 2D grid matching the poles grid.

### 2.4 Tensor-Product Surfaces

`AtomicSurface` is a tensor-product surface: it has independent knot
vectors, degrees, and control-point counts in U and V. A point `S(u, v)` is
evaluated by:

1. Computing U basis functions at parameter `u`.
2. Computing V basis functions at parameter `v`.
3. Combining them over the 2D control-point grid with weights.

This means U and V are fully decoupled — you can have degree 2 in U
(following a circle) and degree 1 in V (a straight ruling) in the same
surface. This is exactly what `RuledSurface` does.

---

## 3. Worked Example — RuledSurface Between Two Circles

This traces the full path from user-facing component call to GLB triangles.

### 3.1 Input

```python
circle_a = AtomicCircle(plane_bottom, radius=2.0)
circle_b = AtomicCircle(plane_top, radius=3.0)
surface = RuledSurface(circle_a, circle_b)
```

### 3.2 Curve Unification

`RuledSurface.generate()` calls `as_nurbs_curve()` on both inputs. For a
circle, the unifier calls `_arc_like_to_nurbs(plane, radius, 0, 2π)`:

1. The full 2π sweep is split into **4 quarter-arc segments** (each ≤ π/2).
2. Each segment produces 3 control points: start (on-curve, weight 1),
   weighted midpoint (off-curve, weight = cos(π/4) ≈ 0.707), and end
   (on-curve, weight 1). Adjacent segments share endpoints.
3. Result: **9 control points**, degree 2, knots `(0, 0.25, 0.5, 0.75, 1)`
   with multiplicities `(3, 2, 2, 2, 3)`.

This is mathematically exact — the NURBS curve passes through the same
points as the original `AtomicCircle` to machine precision.

### 3.3 Surface Construction

`RuledSurface` validates that both profiles have matching degree, control
point count, and knot structure, then builds:

```python
AtomicSurface(
    poles       = (profile_a.poles, profile_b.poles),   # 2 rows × 9 cols
    weights     = (profile_a.weights, profile_b.weights),
    u_knots     = (0.0, 0.25, 0.5, 0.75, 1.0),        # from the circle
    v_knots     = (0.0, 1.0),                           # ruling direction
    u_mults     = (3, 2, 2, 2, 3),
    v_mults     = (2, 2),
    u_degree    = 2,          # quadratic — follows the circle exactly
    v_degree    = 1,          # linear — straight ruling between curves
)
```

### 3.4 Tessellation for GLB Export

The GLB exporter must convert this mathematical surface into triangles.
It samples the surface on a grid of `(u, v)` parameter values.

**Knot-span-aware sampling** (implemented in `_surface_parameter_samples`):

- Collect all unique knot values in the active parameter range as
  mandatory sample boundaries.
- Within each knot span, add interior samples proportional to the degree.
- The density per span is governed by `_SURFACE_SUBDIVS_PER_SPAN`:

| Degree | Subdivisions per span | Rationale |
|---|---|---|
| 1 | 1 | Linear — span endpoints are sufficient |
| 2 | 16 | Matches standalone circle quality (4 spans × 16 = 64 ≈ `_CIRCLE_SEGS`) |
| 3 | 12 | Cubic curves need fewer samples per span for equivalent smoothness |

For the ruled-surface example:

- **U direction** (degree 2, 4 spans): 4 × 16 + 1 = **65 samples** along
  the circle.
- **V direction** (degree 1, 1 span): 1 × 1 + 1 = **2 samples** (top and
  bottom edge). No wasted intermediate rows.
- Total: 65 × 2 = **130 vertices**, **128 triangles**.

Compare to the old uniform approach (24 × 12 grid): 325 vertices, 576
triangles — most of them wasted on the linear V direction.

---

## 4. The Conversion Pipeline

Geometry in pyhopper flows through three layers:

```
Named-Shape Atoms          AtomicCircle, AtomicLine, AtomicArc, AtomicPolyline
       │
       │  as_nurbs_curve()        ← Utils/Unifiers/unitypes.py
       ▼
Canonical NURBS            AtomicNurbsCurve  (curves)
                           AtomicSurface     (surfaces, built from NURBS profiles)
       │
       │  _tessellate_*()         ← Utils/Exporters/glb.py
       ▼
Display Geometry           vertex/index arrays → GLB triangles or line strips
```

### 4.1 Unifiers (`Utils/Unifiers/`)

A **unifier** converts a named-shape atom into the canonical NURBS form so
that downstream operations can work with a single type. The current unifier
is `as_nurbs_curve()`.

Current conversion table:

| Input type | Output degree | How |
|---|---|---|
| `AtomicLine` | 1 | 2 control points, knots `[0,0,1,1]` |
| `AtomicPolyline` | 1 | N control points, open uniform knots |
| `AtomicCircle` | 2 | 9 weighted CPs, 4 quarter-arc spans |
| `AtomicArc` | 2 | Weighted CPs, 1–4 spans depending on sweep |
| `AtomicNurbsCurve` | preserved | Knot normalization and weight fill |

**Contract for new unifiers:**

- Every new named-shape curve atom must have a corresponding conversion in
  `as_nurbs_curve()` before it can be used with any surface or advanced
  curve operation.
- Unifiers must produce mathematically exact conversions — no
  approximation, no sampling. The NURBS output must represent the identical
  curve.
- Unifiers must produce clamped knot vectors (multiplicity = degree + 1 at
  both ends).
- Weights must always be populated (default to 1.0 for non-rational input).
- Knots must be stored as the full expanded vector on `AtomicNurbsCurve`
  (this is what the atom's dataclass expects), but surfaces use the
  unique+multiplicity OCCT form.

### 4.2 Future: Surface Unifiers

As surface types grow (lofts, sweeps, extrusions, revolutions), we will
need `as_nurbs_surface()` — a surface-level unifier analogous to
`as_nurbs_curve()`. Today, surfaces are always constructed directly as
`AtomicSurface` inside components like `RuledSurface`. But when build123d
enters the picture, its BRep faces will need conversion back to
`AtomicSurface` for the pyhopper data model.

---

## 5. The Adapter Layer — Bridging to Geometry Kernels

`Utils/Adapters/` exists as a placeholder. This is where the bridge between
pyhopper's atom world and external geometry libraries lives.

### 5.1 What Adapters Do

An **adapter** translates between pyhopper atoms and the native types of an
external geometry library. Adapters are always bidirectional:

```
pyhopper Atom  ──adapt_to_kernel()──►  kernel-native object
                                             │
                                        kernel operation
                                             │
pyhopper Atom  ◄──adapt_from_kernel()──  kernel-native result
```

### 5.2 The build123d Adapter (Future)

build123d will be the backend for operations that are too hard to implement
from scratch: extrusions, lofts, booleans, chamfers, fillets, and shelling.

The adapter contract for build123d:

```
Utils/Adapters/
└── build123d_adapter.py
    ├── curve_to_b123d(atom) -> build123d Edge/Wire
    │     Converts AtomicNurbsCurve → build123d NURBS edge.
    │     Always go through as_nurbs_curve() first — never convert
    │     named shapes directly to avoid duplicating conversion logic.
    │
    ├── surface_to_b123d(atom) -> build123d Face
    │     Converts AtomicSurface → build123d BSpline face.
    │
    ├── b123d_to_curve(edge) -> AtomicNurbsCurve
    │     Extracts NURBS data from a build123d edge result.
    │
    ├── b123d_to_surface(face) -> AtomicSurface
    │     Extracts pole grid, knots, weights from a build123d BSpline face.
    │
    └── b123d_to_mesh(shape) -> AtomicMesh
          Tessellates a build123d shape into an AtomicMesh for display
          when the NURBS representation is not needed or not available.
```

**Critical rules for the build123d adapter:**

1. **Unify before adapting.** The adapter accepts only canonical types
   (`AtomicNurbsCurve`, `AtomicSurface`). Named-shape atoms must pass
   through a unifier first. This keeps the adapter surface area small and
   avoids N×M conversion paths.

2. **Never store kernel objects in atoms.** Atoms are frozen, serializable,
   and kernel-independent. The adapter creates kernel objects on the fly,
   runs the operation, and extracts results back into atoms immediately.

3. **Adapters are stateless functions, not classes.** No caching, no
   sessions. Each call is independent.

4. **Graceful absence.** build123d is an optional dependency. Any component
   that uses the adapter must handle `ImportError` at module load and
   report a clear error ("this component requires build123d") rather than
   crashing with a missing-module traceback.

### 5.3 Adapter–Unifier Separation

The division of responsibilities:

| Layer | Responsibility | Example |
|---|---|---|
| **Unifier** | Convert between pyhopper atom types (no external deps) | `AtomicCircle` → `AtomicNurbsCurve` |
| **Adapter** | Convert between pyhopper atoms and kernel-native types | `AtomicNurbsCurve` → build123d `Edge` |
| **Component** | Orchestrate: unify → adapt → kernel op → adapt back | `Extrude(curve, vector)` |

A component never calls both a unifier and an adapter on the same input —
the adapter's input contract requires already-unified types. The component
calls the unifier, then hands the result to the adapter.

---

## 6. Tessellation Contract

Tessellation converts mathematical NURBS geometry into discrete
vertex/triangle data for display and export. It happens only in the export
layer — never inside components, never inside atoms.

### 6.1 Rules

1. **Knot-span awareness.** Every unique knot value in the active parameter
   range is a mandatory sample point. Interior samples are distributed
   within each span, never across span boundaries.

2. **Degree-adaptive density.** Linear spans (degree 1) get no interior
   samples. Higher-degree spans get progressively more, governed by
   `_SURFACE_SUBDIVS_PER_SPAN`.

3. **Independent per direction.** U and V tessellation are computed
   separately. A surface that is degree 3 in U and degree 1 in V must not
   waste samples on the linear direction.

4. **Consistent with curve display.** Surface boundary edges must have
   comparable visual quality to standalone curve rendering. The current
   calibration: degree-2 spans use 16 subdivisions, which produces 65
   samples for a full NURBS circle (4 spans) — matching the 64 segments
   used for `AtomicCircle` wireframe display.

5. **No tessellation in atoms or components.** Tessellation is a display
   concern. Atoms store exact geometry; components produce exact geometry.
   Only exporters and renderers tessellate.

### 6.2 Future: Curvature-Adaptive Tessellation

The current span-based approach is a significant improvement over uniform
sampling but still allocates the same number of samples to every span of
the same degree, regardless of actual curvature. A future refinement could:

- Evaluate the surface at span midpoints and quarter-points.
- Compute chord deviation (distance from the linear interpolant to the
  actual surface point).
- Subdivide spans whose deviation exceeds a threshold.
- Skip interior samples for spans that are nearly flat.

This is a display-quality optimization and does not affect the atom or
component layers.

---

## 7. Contract for New Curve and Surface Components

### 7.1 Adding a New Curve Type

1. If the curve is a common named shape (ellipse, helix, etc.), create a
   new frozen-dataclass atom in `Core/Atoms.py` with human-readable fields.
2. Add a conversion path in `Utils/Unifiers/unitypes.as_nurbs_curve()` that
   produces a mathematically exact `AtomicNurbsCurve`.
3. If the curve needs GLB wireframe display, add a handler in the GLB
   exporter. Prefer converting to NURBS and tessellating via the existing
   NURBS path over writing custom tessellation.
4. Add the atom to the supported-types tuple in the `Curve` parameter
   component (`Components/Params/Geometry/Curve.py`).

### 7.2 Adding a New Surface Component

1. The component's `generate()` must return an `AtomicSurface` (or
   `AtomicMesh` for mesh-only operations).
2. Input curves must be unified via `as_nurbs_curve()` before building the
   surface pole grid. Never reach into named-shape fields (like
   `circle.radius`) to build surface control points.
3. Validate that input profiles are compatible (matching degree, knot
   structure, control-point count) when the surface type requires it.
4. Set `u_degree`, `v_degree`, knots, and multiplicities explicitly. Do not
   rely on `AtomicSurface.__post_init__` auto-generation for surfaces built
   from curve profiles — the knot structure must come from the input curves.

### 7.3 Adding a Kernel-Backed Component (build123d)

1. Place the component under the appropriate tab/category as usual.
2. In `generate()`:
   a. Unify inputs to canonical atom types.
   b. Call adapter functions to convert atoms → kernel objects.
   c. Run the kernel operation.
   d. Call adapter functions to convert results → atoms.
   e. Return the atom(s).
3. Guard the adapter import with a try/except at module level and raise a
   clear `RuntimeError` if the dependency is missing.
4. Never expose kernel-native objects in inputs, outputs, or intermediate
   DataTree values. Everything that enters or leaves a component is an atom.

### 7.4 Degree and Knot Compatibility

When a component combines multiple curves (loft, ruled surface, sweep rail
matching), the profiles must share compatible NURBS structure. The general
strategy:

- **Same degree**: raise an error if degrees differ. Degree elevation is a
  future unifier responsibility, not the component's.
- **Same knot vector**: raise an error if knot structures differ. Knot
  insertion (refinement) is a future unifier responsibility.
- **Same control-point count**: follows from matching degree + knots.

Future unifiers (`elevate_degree`, `refine_knots`, `make_compatible`) will
handle automatic harmonization. Until they exist, components must reject
incompatible inputs with clear error messages.

---

## 8. Roadmap

### Present (what exists now)

- Five curve atom types with full NURBS unification.
- One surface atom type (`AtomicSurface`) with OCCT-style representation.
- One surface component (`RuledSurface`) as proof of the pipeline.
- Knot-span-aware GLB tessellation.
- No adapter layer yet.

### Next Steps

1. **build123d adapter** (`Utils/Adapters/build123d_adapter.py`) — the
   bidirectional bridge. Start with curve and surface conversion, validate
   round-trip fidelity (atom → kernel → atom produces identical NURBS data).

2. **Extrude component** — first build123d-backed component. Takes a curve
   and a vector, returns an `AtomicSurface`. Uses the adapter to run
   `build123d.Extrude`, then extracts the resulting face.

3. **Loft component** — takes N profile curves, returns an `AtomicSurface`.
   Requires the future `make_compatible` unifier to harmonize profiles
   before passing to build123d.

4. **Boolean components** (Union, Difference, Intersection) — operate on
   surfaces/solids. These will likely return `AtomicMesh` initially since
   boolean results may not be representable as single tensor-product
   surfaces.

5. **Degree elevation and knot refinement unifiers** — enable automatic
   profile harmonization so lofts and sweeps can accept curves with
   different structures.

6. **Curvature-adaptive tessellation** — refine the GLB export to use chord
   deviation rather than fixed per-span counts.

---

## 9. Summary of Rules

1. Atoms are pure data. No behavior, no kernel objects, no mutation.
2. Named-shape atoms exist for user ergonomics. NURBS is the canonical
   internal representation for all curve/surface operations.
3. Unifiers convert between atom types without external dependencies and
   without approximation.
4. Adapters convert between atoms and kernel-native types. They are
   stateless, bidirectional, and handle optional dependencies gracefully.
5. Components orchestrate: unify → (adapt → kernel op → adapt back) →
   return atoms.
6. Tessellation happens only in the export/display layer, never in
   components.
7. Knot structure matters. Tessellation must respect span boundaries.
   Display quality must be consistent between standalone curves and
   surface edges.
8. Every new curve type needs a unifier entry. Every new surface component
   must work with unified NURBS profiles. Every kernel-backed component
   must go through the adapter layer.
