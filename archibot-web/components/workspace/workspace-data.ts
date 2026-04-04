export const AREA_INSET = 12;
export const SUBAREA_GAP = 16;
export const SUBAREA_MIN_WIDTH = 152;
export const SUBAREA_MIN_HEIGHT = 104;
export const FRAME_CONTENT_OFFSET_X = 26;
export const FRAME_CONTENT_OFFSET_Y = 86;
export const FRAME_RIGHT_PADDING = 26;
export const FRAME_BOTTOM_PADDING = 26;

export type WorkspaceSeedSubdomainTemplate = {
  slug: string;
  name: string;
  description: string;
  type: string;
};

export type WorkspaceSeedAreaTemplate = {
  slug: string;
  name: string;
  description: string;
  type: string;
  seedX: number;
  seedY: number;
  seedWidth: number;
  subdomains: WorkspaceSeedSubdomainTemplate[];
};

export type SeededWorkspaceArea = {
  slug: string;
  name: string;
  description: string;
  type: string;
  order: number;
  subdomains: Array<WorkspaceSeedSubdomainTemplate & {
    order: number;
    x: number;
    y: number;
    w: number;
    h: number;
  }>;
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function hashString(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function seededUnit(seed: string) {
  return (hashString(seed) % 10000) / 10000;
}

export function buildInitialSubAreaLayouts(
  sectionSlug: string,
  items: WorkspaceSeedSubdomainTemplate[],
  width: number,
) {
  const columns = width >= 320 ? 2 : 1;
  const laneWidth = columns === 1
    ? width - AREA_INSET * 2
    : (width - AREA_INSET * 2 - SUBAREA_GAP) / 2;
  const rowStride = 128;

  return items.map((item, index) => {
    const column = columns === 1 ? 0 : index % columns;
    const row = Math.floor(index / columns);
    const widthSeed = seededUnit(`${sectionSlug}:${item.slug}:w`);
    const heightSeed = seededUnit(`${sectionSlug}:${item.slug}:h`);
    const offsetXSeed = seededUnit(`${sectionSlug}:${item.slug}:x`);
    const offsetYSeed = seededUnit(`${sectionSlug}:${item.slug}:y`);
    const naturalWidth = clamp(164 + widthSeed * 42, SUBAREA_MIN_WIDTH, Math.max(164, laneWidth));
    const naturalHeight = clamp(112 + heightSeed * 34, SUBAREA_MIN_HEIGHT, 154);
    const laneOffset = columns === 1 ? 0 : column * (laneWidth + SUBAREA_GAP);
    const jitterX = columns === 1 ? 0 : (offsetXSeed - 0.5) * 14;
    const jitterY = (offsetYSeed - 0.5) * 18;

    return {
      x: AREA_INSET + laneOffset + jitterX,
      y: AREA_INSET + row * rowStride + jitterY,
      w: naturalWidth,
      h: naturalHeight,
    };
  });
}

export const WORKSPACE_SEED_TEMPLATE: WorkspaceSeedAreaTemplate[] = [
  {
    slug: "inputs-definition",
    name: "Inputs & Definition",
    description: "",
    type: "Form",
    seedX: -540,
    seedY: -260,
    seedWidth: 320,
    subdomains: [
      { slug: "project-brief", name: "Project Brief", description: "", type: "subdomain" },
      { slug: "stakeholders-users", name: "Stakeholders & Users", description: "", type: "subdomain" },
      { slug: "project-constraints", name: "Project Constraints", description: "", type: "subdomain" },
      { slug: "deliverable-intent", name: "Deliverable Intent", description: "", type: "subdomain" },
    ],
  },
  {
    slug: "site-analysis",
    name: "Site Analysis",
    description: "",
    type: "Layers",
    seedX: -120,
    seedY: -340,
    seedWidth: 360,
    subdomains: [
      { slug: "geolocation-parcel", name: "Geolocation & Parcel Definition", description: "", type: "subdomain" },
      { slug: "topography", name: "Topography", description: "", type: "subdomain" },
      { slug: "climate-sun-wind", name: "Climate, Sun & Wind", description: "", type: "subdomain" },
      { slug: "access-mobility", name: "Access & Mobility", description: "", type: "subdomain" },
      { slug: "context-surroundings", name: "Context & Surroundings", description: "", type: "subdomain" },
      { slug: "vegetation-ecology", name: "Vegetation & Ecology", description: "", type: "subdomain" },
      { slug: "site-opportunities-risks", name: "Site Opportunities & Risks", description: "", type: "subdomain" },
    ],
  },
  {
    slug: "programme",
    name: "Programme",
    description: "",
    type: "Sheets",
    seedX: 330,
    seedY: -300,
    seedWidth: 420,
    subdomains: [
      { slug: "spatial-programme-table", name: "Spatial Programme Table", description: "", type: "subdomain" },
      { slug: "functional-grouping", name: "Functional Grouping", description: "", type: "subdomain" },
      { slug: "adjacencies-separation", name: "Adjacencies & Separation Rules", description: "", type: "subdomain" },
      { slug: "regulatory-requirements", name: "Regulatory Requirements", description: "", type: "subdomain" },
      { slug: "setbacks-envelope-buildability", name: "Setbacks, Envelope & Buildability Rules", description: "", type: "subdomain" },
      { slug: "financial-area-feasibility", name: "Financial & Area Feasibility", description: "", type: "subdomain" },
      { slug: "programme-synthesis", name: "Programme Synthesis", description: "", type: "subdomain" },
    ],
  },
  {
    slug: "concept-intent",
    name: "Concept & Design Intent",
    description: "",
    type: "Canvas",
    seedX: -420,
    seedY: 80,
    seedWidth: 380,
    subdomains: [
      { slug: "design-drivers", name: "Design Drivers", description: "", type: "subdomain" },
      { slug: "concept-narrative", name: "Concept Narrative", description: "", type: "subdomain" },
      { slug: "spatial-principles", name: "Spatial Principles", description: "", type: "subdomain" },
      { slug: "environmental-strategy", name: "Environmental Strategy", description: "", type: "subdomain" },
      { slug: "morphological-intent", name: "Morphological Intent", description: "", type: "subdomain" },
    ],
  },
  {
    slug: "spatial-configuration",
    name: "Spatial Configuration",
    description: "",
    type: "Canvas",
    seedX: 70,
    seedY: 90,
    seedWidth: 340,
    subdomains: [
      { slug: "bubble-diagramming", name: "Bubble Diagramming", description: "", type: "subdomain" },
      { slug: "site-zoning-massing", name: "Site Zoning & Massing", description: "", type: "subdomain" },
      { slug: "vertical-distribution", name: "Vertical Distribution", description: "", type: "subdomain" },
      { slug: "circulation", name: "Circulation", description: "", type: "subdomain" },
      { slug: "spatial-evaluation", name: "Spatial Evaluation", description: "", type: "subdomain" },
    ],
  },
  {
    slug: "schematic-design",
    name: "Schematic Design",
    description: "",
    type: "Canvas",
    seedX: 500,
    seedY: 120,
    seedWidth: 320,
    subdomains: [
      { slug: "plan-layout-development", name: "Plan Layout Development", description: "", type: "subdomain" },
      { slug: "sectional-logic", name: "Sectional Logic", description: "", type: "subdomain" },
      { slug: "envelope-facade-principles", name: "Envelope & Facade Principles", description: "", type: "subdomain" },
      { slug: "structural-mep-logic", name: "Structural & MEP Reservation Logic", description: "", type: "subdomain" },
      { slug: "schematic-coordination", name: "Schematic Coordination", description: "", type: "subdomain" },
    ],
  },
  {
    slug: "technical-representation",
    name: "Technical Representation",
    description: "",
    type: "CAD Viewer",
    seedX: -700,
    seedY: 380,
    seedWidth: 360,
    subdomains: [
      { slug: "bim-element-mapping", name: "BIM Element Mapping", description: "", type: "subdomain" },
      { slug: "data-metadata-structuring", name: "Data & Metadata Structuring", description: "", type: "subdomain" },
      { slug: "drawing-extraction-logic", name: "Drawing Extraction Logic", description: "", type: "subdomain" },
      { slug: "technical-validation", name: "Technical Validation", description: "", type: "subdomain" },
    ],
  },
  {
    slug: "final-deliverables",
    name: "Final Deliverables",
    description: "",
    type: "PDF Viewer",
    seedX: -240,
    seedY: 430,
    seedWidth: 320,
    subdomains: [
      { slug: "deliverable-assembly", name: "Deliverable Assembly", description: "", type: "subdomain" },
      { slug: "visualization-presentation", name: "Visualization & Presentation", description: "", type: "subdomain" },
      { slug: "quantities-schedules", name: "Quantities & Schedules", description: "", type: "subdomain" },
    ],
  },
];

export function buildSeededWorkspaceHierarchy(): SeededWorkspaceArea[] {
  return WORKSPACE_SEED_TEMPLATE.map((area, areaIndex) => {
    const layouts = buildInitialSubAreaLayouts(
      area.slug,
      area.subdomains,
      area.seedWidth - FRAME_CONTENT_OFFSET_X - FRAME_RIGHT_PADDING,
    );

    return {
      slug: area.slug,
      name: area.name,
      description: area.description,
      type: area.type,
      order: areaIndex,
      subdomains: area.subdomains.map((item, itemIndex) => ({
        ...item,
        order: itemIndex,
        x: area.seedX + FRAME_CONTENT_OFFSET_X + layouts[itemIndex].x,
        y: area.seedY + FRAME_CONTENT_OFFSET_Y + layouts[itemIndex].y,
        w: layouts[itemIndex].w,
        h: layouts[itemIndex].h,
      })),
    };
  });
}
