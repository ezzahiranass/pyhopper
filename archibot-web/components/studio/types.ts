import type { Node } from "@xyflow/react";

export type AgentJob = string;

export type JobOverview = {
  slug: string;
  title: AgentJob;
  description: string;
  tools: string[];
};

export type PersonalityOption = {
  value: string;
  label: string;
  prompt: string;
};

export type OrgChartItem = {
  id: string;
  parentId: string | null;
  name: string;
  job: AgentJob;
  description: string;
  personality: string;
};

// Agent is the Firestore-persisted form of an OrgChartItem,
// stored as agents/{agentId}. Teams reference active agents by id.
export type Agent = OrgChartItem;

export type OrgChartNodeData = {
  name: string;
  job: AgentJob;
  description: string;
  personality: string;
  personalities: PersonalityOption[];
  isRoot: boolean;
  isEditing: boolean;
  onSelect: () => void;
  onStartEdit: () => void;
  onStopEdit: () => void;
  onAddChild: () => void;
  onDelete: () => void;
  onSubmitEdit: (value: {
    name: string;
    job: AgentJob;
    description: string;
    personality: string;
  }) => void;
};

export type OrgChartFlowNode = Node<OrgChartNodeData, "orgChart">;

export type ProjectAnalysisStatus = "idle" | "running" | "done" | "error";

export type Project = {
  id: string;
  name: string;
  description: string;
  projectType: string;
  createdAt: number;
  parcelDefinition: ProjectParcel | null;
  attachments: ProjectAttachment[];
  analysisStatus: ProjectAnalysisStatus;
  analysisUpToDate: boolean;
};

export type ProjectAttachment = {
  name: string;
  contentType: string;
  size: number;
  url: string;
  storagePath: string;
};

export type ProjectParcel = {
  type: "Polygon";
  coordinates: [number, number][][];
  bbox: [number, number, number, number] | null;
  center: [number, number] | null;
  searchQuery: string;
  analysisRadiusMeters: number;
};

export type NewProjectInput = {
  name: string;
  description: string;
  projectType: string;
  parcelDefinition: ProjectParcel | null;
  attachments: File[];
};

export type UpdateProjectInput = {
  projectId: string;
  name: string;
  description: string;
  projectType: string;
  parcelDefinition: ProjectParcel | null;
  attachmentsToAdd?: File[];
  attachmentsToRemove?: ProjectAttachment[];
};

export type WorkspaceTextArtifact = {
  type: "text";
  label: string;
  value: string;
};

export type GeolocationMapStyle = {
  basemapSaturation?: number;       // -1 (greyscale) to 1 (vivid), default 0
  basemapContrast?: number;         // -1 to 1, default 0
  basemapBrightnessMin?: number;    // 0 to 1, default 0
  basemapBrightnessMax?: number;    // 0 to 1, default 1
  showLabels?: boolean;             // hide all symbol text layers, default true
  showIcons?: boolean;              // hide all symbol icon layers, default true
  backgroundColor?: string;        // map background color, default transparent
};

export type WorkspaceGeolocationArtifact = {
  type: "geolocation";
  label: string;
  value: {
    coordinates: [number, number][][] | null;
    center: [number, number] | null;
    analysisRadiusMeters: number | null;
    // Optional GeoJSON overlay layers, serialized as a JSON string to avoid
    // Firestore nested-entity limits. Parse with JSON.parse before use.
    overlaysGeojson?: string;
    mapStyle?: GeolocationMapStyle;
  };
};

export type WorkspaceImageArtifact = {
  type: "image";
  label: string;
  value: {
    url: string;
    alt?: string;
  };
};

export type WorkspaceModelArtifact = {
  type: "model";
  label: string;
  value: {
    url: string;
    storagePath?: string;
    format?: string;
  };
};

export type GeoJsonFeature = {
  type: "Feature";
  properties: Record<string, unknown>;
  geometry: {
    type: string;
    coordinates: unknown;
  };
};

export type WorkspaceArtifact =
  | WorkspaceTextArtifact
  | WorkspaceGeolocationArtifact
  | WorkspaceImageArtifact
  | WorkspaceModelArtifact;

export type WorkspaceArtifactMap = Record<string, WorkspaceArtifact>;

export type WorkspaceSubdomain = {
  id: string;
  areaId: string;
  slug: string;
  name: string;
  description: string;
  type: string;
  content: string | null;
  artifacts: WorkspaceArtifactMap;
  isLocked: boolean;
  createdBy: string | null;
  createdAt: number;
  order: number;
  x: number;
  y: number;
  w: number;
  h: number;
};

export type WorkspaceArea = {
  id: string;
  slug: string;
  name: string;
  description: string;
  type: string;
  isLocked: boolean;
  createdBy: string | null;
  createdAt: number;
  order: number;
  frameX: number;
  frameY: number;
  frameW: number;
  frameH: number;
  subdomains: WorkspaceSubdomain[];
};

export type Team = {
  id: string;
  name: string;
  createdAt: number;
  orgChart: OrgChartItem[];
  projectIds: string[];
  agentIds: string[];
};
