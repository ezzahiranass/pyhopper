# Graph Snapshot, GraphDocument Contract, and Export Pipeline

## Summary
Implement the graph editor around a single shared graph store that owns `nodes`, `edges`, `viewport`, node-authored values, export status, and the latest `modelUrl`. Persist a debounced snapshot to browser storage on every graph change, restore it on page load, and prove v1 by refreshing the page and confirming nodes, wires, slider values, and viewport come back intact.

Treat XYFlow `toObject()` as the editor snapshot source, but define a versioned `GraphDocument` as the backend contract. The frontend will derive `GraphDocument` from the live graph store and send it through a new export endpoint. The backend will validate the document, compile it into a Python definition function in a separate compiler module, execute it to obtain pyhopper geometry, export a GLB, and return both the GLB URL and generated Python source.

## Key Changes

### 1. Shared graph state and autosave
- Introduce a page-level graph editor provider/store used by both the flow canvas and the Three.js scene.
- Move slider values out of local component state and into node data owned by the shared graph store so `toObject()` captures authored values.
- Keep XYFlow as the editing engine, but make all node, edge, connect, delete, and value-change handlers update the shared store.
- Persist a debounced snapshot to `localStorage` on every meaningful graph change:
  - node add/remove/move
  - edge add/remove
  - node-authored value change
  - viewport change
- Restore from `localStorage` on initial load; if no snapshot exists, start empty.
- Use a single storage key and include a schema version in the persisted document for future migrations.

### 2. Canonical `GraphDocument` contract
Define one backend-facing JSON contract and version it from day one:

```ts
type GraphDocument = {
  schemaVersion: 1;
  graphId: string;
  viewport: { x: number; y: number; zoom: number };
  nodes: GraphNode[];
  edges: GraphEdge[];
};

type GraphNode = {
  id: string;
  kind: "component";
  componentKey: string; // fully qualified python identity
  component: {
    tab: string;
    category: string;
    name: string;
  };
  position: { x: number; y: number };
  values: Record<string, unknown>; // authored literal values owned by this node
};

type GraphEdge = {
  id: string;
  sourceNodeId: string;
  sourcePort: string;
  targetNodeId: string;
  targetPort: string;
};
```

Contract rules:
- `componentKey` is the stable compiler identity and must be a fully qualified Python path/class identity.
- `component.tab/category/name` are descriptive only and not used for resolution.
- `values` contains only authored literals. In v1 that means slider-authored values for zero-input presets like `NumberSlider`.
- Derived data is never persisted: no computed outputs, no preview geometry, no resolved defaults.
- Handle names in edges must match declared input/output port names exactly.
- The frontend may still keep a raw XYFlow snapshot for convenience, but the POST body sent to the backend is `GraphDocument`.

### 3. Catalog/API contract hardening
- Extend the `/components` payload so every component includes a stable compiler identity field, based on Python module/class path.
- Keep existing UI metadata, but stop treating `tab/category/component` as the canonical identity.
- Ensure preset metadata needed by the frontend remains declarative; authored values live in the graph state, not in the catalog.

### 4. Export UX and frontend flow
- Add a bottom-right floating export button on the flow canvas using `lucide-react`.
- The button reads the current shared graph state, derives a `GraphDocument`, and POSTs it to the backend.
- The button shows busy/error state and prevents duplicate exports while a request is in flight.
- On successful export:
  - store the returned `glb_url` in shared state
  - update the Three.js scene to load the new model
  - optionally expose returned generated Python source in state for debugging/logging even if not rendered yet
- Remove the current scene-side test trigger from the main export path; the scene becomes a consumer of the exported result, not the initiator.

### 5. Backend compiler and export pipeline
- Add a dedicated compiler module whose only job is `GraphDocument -> Python definition source`.
- Compiler responsibilities:
  - validate schema version and required fields
  - resolve each `componentKey` to a pyhopper component
  - validate that every edge references real nodes and declared ports
  - validate that each required input is satisfied by:
    - an incoming connection, or
    - a declared component default, or
    - an authored literal in `values`
  - reject unsupported authored literals in v1 except slider-backed values
  - topologically sort nodes; fail with a clear error on cycles
  - generate deterministic Python source with one variable per node and keyword arguments by input name
  - generate a function that returns the final scene geometry to export
- Execution responsibilities:
  - execute the generated definition in a controlled module namespace with required imports
  - obtain pyhopper geometry
  - pass it to `export_glb`
  - write the GLB to the generated output directory
- New export endpoint:
  - `POST /graphs/export`
  - request body: `GraphDocument`
  - success response: `glb_url`, file metadata, generated Python source, and optionally the accepted `graphId`/`schemaVersion`
  - validation failure: HTTP 400 with a structured `errors` array
  - compiler/runtime failure: HTTP 500 with a structured error payload suitable for frontend display

## Public Interfaces
- `/components` response adds a stable Python-path-based component identity field.
- New `POST /graphs/export` endpoint accepts `GraphDocument`.
- Frontend types add:
  - `GraphDocument`
  - `GraphNode`
  - `GraphEdge`
  - shared node data shape that includes authored `values`
- `ComponentNode` receives value and value-change callbacks from shared state instead of owning slider state internally.

## Test Plan
- Refresh persistence:
  - add nodes, wire them, change at least one slider value, move the canvas, refresh, verify exact restoration
- GraphDocument derivation:
  - confirm a saved/posted document contains stable `componentKey`, positions, viewport, edges by handle name, and authored slider values
- Export success:
  - build a valid graph using supported v1 inputs, export, receive `glb_url` and generated Python source, and load the returned GLB in the scene
- Validation failures:
  - missing required input
  - edge references invalid node or port
  - cycle in graph
  - unsupported literal value on a non-slider node
- Determinism:
  - same graph produces stable generated Python ordering across repeated exports
- Backward compatibility:
  - app handles absent local snapshot cleanly
  - app ignores or rejects unsupported persisted schema versions with a clear reset path

## Assumptions and Defaults
- Autosave persistence in v1 is browser-local only; no backend draft storage yet.
- Export response in v1 returns both GLB metadata/URL and generated Python source.
- Stable component identity is a fully qualified Python path/class identity, not the UI tuple.
- V1 authored literals are limited to slider-backed zero-input presets plus normal component defaults; other unconnected required inputs fail validation.
- The export action lives on the canvas bottom-right and updates the scene through shared page state.
