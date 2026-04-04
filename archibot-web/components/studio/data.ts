import { AgentJob, JobOverview, OrgChartItem, PersonalityOption } from "@/components/studio/types";

export const FALLBACK_JOB_OVERVIEWS: JobOverview[] = [
  {
    slug: "manager",
    title: "Manager",
    description: "Sets strategy, coordinates the team, reviews output, and keeps delivery aligned with project goals.",
    tools: ["edit_company_hierarchy", "view_company_info"],
  },
  {
    slug: "administrative_assistant",
    title: "Administrative Assistant",
    description: "Handles team coordination, tracks administrative details, and can retrieve project and studio information when needed.",
    tools: ["get_current_team_context", "view_company_info"],
  },
  {
    slug: "computational_designer",
    title: "Computational Designer",
    description: "Builds computational workflows, automations, and generative design systems to support design exploration and analysis.",
    tools: ["view_company_info"],
  },
  {
    slug: "archviz_artist",
    title: "Archviz Artist",
    description: "Creates architectural visualizations, atmospheres, presentation imagery, and short motion studies that communicate design intent clearly and convincingly.",
    tools: ["generate_archviz_image", "generate_archviz_video", "view_company_info"],
  },
  {
    slug: "senior_architect",
    title: "Senior Architect",
    description: "Leads architectural design decisions, develops project direction, and reviews work for technical and spatial quality.",
    tools: [],
  },
  {
    slug: "junior_architect",
    title: "Junior Architect",
    description: "Supports design development, modeling, documentation, and coordination under senior guidance.",
    tools: ["view_company_info"],
  },
];

export const FALLBACK_PERSONALITIES: PersonalityOption[] = [
  { value: "funny", label: "Funny", prompt: "" },
  { value: "serious", label: "Serious", prompt: "" },
  { value: "clumsy", label: "Clumsy", prompt: "" },
  { value: "confident", label: "Confident", prompt: "" },
];

const DEFAULT_AGENT_NAMES = [
  "Avery Brooks",
  "Jordan Lee",
  "Taylor Reed",
  "Morgan Ellis",
  "Cameron Blake",
  "Riley Hayes",
  "Quinn Parker",
  "Casey Morgan",
];

export function getJobDescription(job: AgentJob, jobs: JobOverview[] = FALLBACK_JOB_OVERVIEWS) {
  return jobs.find((item) => item.title === job)?.description ?? "";
}

export function isAgentJob(value: string, jobs: JobOverview[] = FALLBACK_JOB_OVERVIEWS): value is AgentJob {
  return jobs.some((item) => item.title === value);
}

export function createAgentName(index: number) {
  return DEFAULT_AGENT_NAMES[index % DEFAULT_AGENT_NAMES.length] ?? `Agent ${index + 1}`;
}

export function createAgentJob(index: number, jobs: JobOverview[] = FALLBACK_JOB_OVERVIEWS): AgentJob {
  return jobs[index % jobs.length]?.title ?? "Junior Architect";
}

export function createDefaultManagerNode(
  jobs: JobOverview[] = FALLBACK_JOB_OVERVIEWS,
): OrgChartItem {
  const managerJob = jobs.find((item) => item.title === "Manager")?.title ?? "Manager";

  return {
    id: "manager",
    parentId: null,
    name: createAgentName(0),
    job: managerJob,
    description: getJobDescription(managerJob, jobs),
    personality: "",
  };
}
