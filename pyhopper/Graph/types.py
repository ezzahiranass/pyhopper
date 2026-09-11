from __future__ import annotations

from typing import Any, Literal, TypedDict


PortOperation = Literal["Graft", "Simplify", "Flatten", "Reverse", "Reparametrize"]


class PyhopperComponentPort(TypedDict, total=False):
    name: str
    type: str | None
    accepts: list[str] | None
    access: str
    default: Any
    optional: bool


class PyhopperComponentSetting(TypedDict, total=False):
    choices: list[str]
    default: Any
    label: str
    max: float
    min: float
    type: Literal["bool", "choice", "float", "int", "string"]


class PyhopperComponentDefinition(TypedDict, total=False):
    component_key: str
    tab: str
    category: str
    component: str
    description: str
    settings_schema: dict[str, PyhopperComponentSetting]
    settings_defaults: dict[str, Any]
    initial_settings: dict[str, Any]
    initial_values: dict[str, Any]
    input_count: int
    output_count: int
    variadic_inputs: bool
    inputs: list[PyhopperComponentPort]
    outputs: list[PyhopperComponentPort]


class SceneObjectMetadata(TypedDict):
    createdByCommand: str
    locked: bool
    tags: list[str]
    visible: bool


class SceneObjectTransform(TypedDict):
    matrix: list[float]
    pivot: list[float]
    position: list[float]
    rotation: list[float]
    scale: list[float]


class SerializedAtom(TypedDict, total=False):
    type: str


class SceneObject(TypedDict):
    id: str
    metadata: SceneObjectMetadata
    name: str
    revision: int
    transform: SceneObjectTransform
    atom: SerializedAtom


class SceneDocument(TypedDict):
    schemaVersion: Literal[3]
    objects: dict[str, SceneObject]


class GraphViewport(TypedDict):
    x: float
    y: float
    zoom: float


class ComponentGraphNode(TypedDict):
    id: str
    kind: Literal["component"]
    componentKey: str
    component: dict[str, str]
    position: dict[str, float]
    previewEnabled: bool
    settings: dict[str, Any]
    values: dict[str, Any]
    portOperations: dict[str, PortOperation]


class ObjectReferenceGraphNode(TypedDict):
    id: str
    kind: Literal["object-reference"]
    objectId: str
    position: dict[str, float]
    previewEnabled: bool
    portOperations: dict[str, PortOperation]


GraphNode = ComponentGraphNode | ObjectReferenceGraphNode


class GraphEdge(TypedDict):
    id: str
    sourceNodeId: str
    sourcePort: str
    targetNodeId: str
    targetPort: str


class GraphDocument(TypedDict):
    schemaVersion: Literal[2]
    graphId: str
    scene: SceneDocument
    viewport: GraphViewport
    nodes: list[GraphNode]
    edges: list[GraphEdge]
