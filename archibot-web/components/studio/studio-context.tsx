"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  addDoc,
  arrayUnion,
  collection,
  doc,
  documentId,
  onSnapshot,
  query,
  setDoc,
  updateDoc,
  where,
  writeBatch,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import { deleteObject, getDownloadURL, ref, uploadBytes } from "firebase/storage";
import { useAuth } from "@/components/auth-provider";
import {
  createDefaultManagerNode,
  FALLBACK_JOB_OVERVIEWS,
  FALLBACK_PERSONALITIES,
} from "@/components/studio/data";
import {
  JobOverview,
  NewProjectInput,
  OrgChartItem,
  PersonalityOption,
  Project,
  ProjectAnalysisStatus,
  ProjectAttachment,
  ProjectParcel,
  Team,
  UpdateProjectInput,
} from "@/components/studio/types";
import { type NotificationItem } from "@/components/ui/notification";
import {
  DEFAULT_STUDIO_TAB,
  getStudioTabHref,
  isStudioTab,
  type StudioTab,
} from "@/components/studio/studio-tabs";
import { seedProjectWorkspace } from "@/components/workspace/workspace-store";
import { storage } from "@/lib/firebase";

const STUDIO_SETTINGS_STORAGE_KEY = "studio-settings:v1";

type StudioSettings = {
  optimizeCanvasEmbeds: boolean;
};

const DEFAULT_STUDIO_SETTINGS: StudioSettings = {
  optimizeCanvasEmbeds: true,
};

function readStudioSettings(): StudioSettings {
  if (typeof window === "undefined") return DEFAULT_STUDIO_SETTINGS;

  try {
    const raw = window.localStorage.getItem(STUDIO_SETTINGS_STORAGE_KEY);
    if (!raw) return DEFAULT_STUDIO_SETTINGS;

    const parsed = JSON.parse(raw) as Partial<StudioSettings> | null;
    if (!parsed || typeof parsed !== "object") return DEFAULT_STUDIO_SETTINGS;

    return {
      optimizeCanvasEmbeds:
        typeof parsed.optimizeCanvasEmbeds === "boolean"
          ? parsed.optimizeCanvasEmbeds
          : DEFAULT_STUDIO_SETTINGS.optimizeCanvasEmbeds,
    };
  } catch {
    return DEFAULT_STUDIO_SETTINGS;
  }
}

const chatApiBase = process.env.NEXT_PUBLIC_CHAT_API_BASE_URL ?? "http://localhost:5000";

type StudioCtx = {
  loading: boolean;
  activeTab: StudioTab;
  setActiveTab: (tab: StudioTab) => void;
  settings: StudioSettings;
  setOptimizeCanvasEmbeds: (value: boolean) => void;
  jobs: JobOverview[];
  personalities: PersonalityOption[];

  projects: Project[];
  activeProject: Project | null;
  selectedProjectId: string | null;
  selectProject: (id: string | null) => void;
  addProject: (input: NewProjectInput) => Promise<void>;
  updateProject: (input: UpdateProjectInput) => Promise<void>;
  runAnalysis: (projectId: string) => void;

  teams: Team[];
  activeTeamId: string | null;
  selectTeam: (id: string) => void;
  addTeam: (name: string) => Promise<void>;
  updateTeamOrgChart: (teamId: string, items: OrgChartItem[]) => void;

  notifications: NotificationItem[];
  dismissNotification: (id: string) => void;
};

const StudioContext = createContext<StudioCtx | null>(null);

function chunkIds(ids: string[], size = 30) {
  const chunks: string[][] = [];

  for (let index = 0; index < ids.length; index += size) {
    chunks.push(ids.slice(index, index + size));
  }

  return chunks;
}

function normalizeAgent(data: Record<string, unknown>, id: string): OrgChartItem {
  const legacyJob = typeof data.title === "string" ? data.title : "";
  const rawJob = typeof data.job === "string" && data.job ? data.job : legacyJob;
  const job = rawJob || "Junior Architect";
  const name = typeof data.name === "string" && data.name
    ? data.name
    : `Agent ${id.slice(0, 4)}`;

  return {
    id,
    parentId: typeof data.parentId === "string" ? data.parentId : null,
    name,
    job,
    description: typeof data.description === "string" ? data.description : "",
    personality: typeof data.personality === "string" ? data.personality : "",
  };
}

function normalizeLngLatPoint(value: unknown): [number, number] | null {
  if (Array.isArray(value) && value.length >= 2) {
    return [Number(value[0]), Number(value[1])];
  }

  if (value && typeof value === "object") {
    const point = value as { lng?: unknown; lon?: unknown; lat?: unknown };
    const lng = point.lng ?? point.lon;
    if (lng !== undefined && point.lat !== undefined) {
      return [Number(lng), Number(point.lat)];
    }
  }

  return null;
}

function normalizeProjectCoordinates(value: unknown): [number, number][][] {
  if (!Array.isArray(value)) return [];

  return value
    .map((ring) => {
      if (Array.isArray(ring)) {
        return ring
          .map((point) => normalizeLngLatPoint(point))
          .filter((point): point is [number, number] => Boolean(point));
      }

      if (ring && typeof ring === "object") {
        const firestoreRing = ring as { points?: unknown };
        if (Array.isArray(firestoreRing.points)) {
          return firestoreRing.points
            .map((point) => normalizeLngLatPoint(point))
            .filter((point): point is [number, number] => Boolean(point));
        }
      }

      return [];
    })
    .filter((ring): ring is [number, number][] => ring.length > 0);
}

function serializeProjectCoordinates(coordinates: [number, number][][]) {
  return coordinates.map((ring) => ({
    points: ring.map(([lng, lat]) => ({ lng, lat })),
  }));
}

function normalizeProjectParcel(value: unknown): ProjectParcel | null {
  if (!value || typeof value !== "object") return null;

  const parcel = value as {
    type?: unknown;
    coordinates?: unknown;
    bbox?: unknown;
    center?: unknown;
    searchQuery?: unknown;
    analysisRadiusMeters?: unknown;
  };

  const coordinates = normalizeProjectCoordinates(parcel.coordinates);

  const bbox =
    Array.isArray(parcel.bbox) && parcel.bbox.length === 4
      ? [
          Number(parcel.bbox[0]),
          Number(parcel.bbox[1]),
          Number(parcel.bbox[2]),
          Number(parcel.bbox[3]),
        ] as [number, number, number, number]
      : null;

  const center =
    Array.isArray(parcel.center) && parcel.center.length === 2
      ? [Number(parcel.center[0]), Number(parcel.center[1])] as [number, number]
      : null;

  if (parcel.type !== "Polygon" || coordinates.length === 0) return null;

  return {
    type: "Polygon",
    coordinates,
    bbox,
    center,
    searchQuery: typeof parcel.searchQuery === "string" ? parcel.searchQuery : "",
    analysisRadiusMeters:
      typeof parcel.analysisRadiusMeters === "number"
        ? parcel.analysisRadiusMeters
        : Number(parcel.analysisRadiusMeters) || 1000,
  };
}

function serializeProjectParcel(parcel: ProjectParcel | null) {
  if (!parcel) return null;

  return {
    type: "Polygon" as const,
    coordinates: serializeProjectCoordinates(parcel.coordinates),
    bbox: parcel.bbox,
    center: parcel.center,
    searchQuery: parcel.searchQuery,
    analysisRadiusMeters: parcel.analysisRadiusMeters,
  };
}

function normalizeProjectAttachments(value: unknown): ProjectAttachment[] {
  if (!Array.isArray(value)) return [];

  return value
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const attachment = item as Record<string, unknown>;
      const name = typeof attachment.name === "string" ? attachment.name : "";
      const url = typeof attachment.url === "string" ? attachment.url : "";
      const storagePath = typeof attachment.storagePath === "string" ? attachment.storagePath : "";
      if (!name || !url || !storagePath) return null;

      return {
        name,
        url,
        storagePath,
        contentType: typeof attachment.contentType === "string" ? attachment.contentType : "",
        size: typeof attachment.size === "number" ? attachment.size : Number(attachment.size) || 0,
      };
    })
    .filter((item): item is ProjectAttachment => Boolean(item));
}

async function runInitialProjectAnalysis({
  projectId,
  name,
  description,
  projectType,
  parcelDefinition,
}: {
  projectId: string;
  name: string;
  description: string;
  projectType: string;
  parcelDefinition: ProjectParcel | null;
}) {
  const response = await fetch(`${chatApiBase}/projects/autorun-initial-analysis`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      projectId,
      name,
      description,
      projectType,
      siteCoordinates: parcelDefinition?.coordinates ?? null,
      siteCenter: parcelDefinition?.center ?? null,
      analysisRadius: parcelDefinition?.analysisRadiusMeters ?? null,
    }),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { error?: string };
    throw new Error(payload.error || "Initial project analysis failed.");
  }
}

export function StudioProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<JobOverview[]>(FALLBACK_JOB_OVERVIEWS);
  const [personalities, setPersonalities] = useState<PersonalityOption[]>(FALLBACK_PERSONALITIES);
  const [settings, setSettings] = useState<StudioSettings>(readStudioSettings);

  const [projects, setProjects] = useState<Project[]>([]);
  const [teamIds, setTeamIds] = useState<string[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [activeTeamId, setActiveTeamId] = useState<string | null>(null);
  const [selectedProjectIdState, setSelectedProjectIdState] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const prevAnalysisStatuses = useRef<Record<string, ProjectAnalysisStatus>>({});

  // Watch for analysisStatus transitions and manage notifications.
  useEffect(() => {
    const prev = prevAnalysisStatuses.current;

    setNotifications((existing) => {
      let next = [...existing];

      for (const project of projects) {
        const prevStatus = prev[project.id];
        const nextStatus = project.analysisStatus;
        const loadingId = `analysis-loading-${project.id}`;

        if (prevStatus !== "running" && nextStatus === "running") {
          // Add persistent loading notification if not already present.
          if (!next.some((n) => n.id === loadingId)) {
            next = [
              ...next,
              {
                id: loadingId,
                variant: "loading" as const,
                title: "Running site analysis…",
                description: project.name,
              },
            ];
          }
        } else if (prevStatus === "running" && nextStatus === "done") {
          // Replace loading notification with success.
          next = next.filter((n) => n.id !== loadingId);
          next = [
            ...next,
            {
              id: `analysis-done-${project.id}-${Date.now()}`,
              variant: "success" as const,
              title: "Site analysis complete",
              description: project.name,
            },
          ];
        } else if (prevStatus === "running" && nextStatus === "error") {
          // Replace loading notification with error.
          next = next.filter((n) => n.id !== loadingId);
          next = [
            ...next,
            {
              id: `analysis-error-${project.id}-${Date.now()}`,
              variant: "error" as const,
              title: "Site analysis failed",
              description: project.name,
            },
          ];
        }

        prev[project.id] = nextStatus;
      }

      return next;
    });
  }, [projects]);

  const dismissNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const writeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const firestoreAgentIds = useRef<Record<string, Set<string>>>({});
  const agentCache = useRef<Record<string, Map<string, OrgChartItem>>>({});
  const pathSegments = pathname.split("/").filter(Boolean);
  const tabSegment = pathSegments[1];
  const activeTab = isStudioTab(tabSegment) ? tabSegment : DEFAULT_STUDIO_TAB;

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STUDIO_SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    let active = true;

    fetch(`${chatApiBase}/jobs/overviews`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Job catalog request failed with status ${response.status}`);
        }

        return response.json() as Promise<{ jobs?: JobOverview[] }>;
      })
      .then((payload) => {
        if (!active || !Array.isArray(payload.jobs) || payload.jobs.length === 0) return;
        setJobs(payload.jobs);
      })
      .catch((error) => {
        console.error("Failed to load job catalog", error);
      });

    fetch(`${chatApiBase}/personalities`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Personality catalog request failed with status ${response.status}`);
        }

        return response.json() as Promise<{ personalities?: PersonalityOption[] }>;
      })
      .then((payload) => {
        if (!active || !Array.isArray(payload.personalities) || payload.personalities.length === 0) return;
        setPersonalities(payload.personalities);
      })
      .catch((error) => {
        console.error("Failed to load personality catalog", error);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!user) {
      setProjects([]);
      setTeamIds([]);
      setTeams([]);
      setActiveTeamId(null);
      setSelectedProjectIdState(null);
      setLoading(false);
      return;
    }

    setDoc(
      doc(db, "users", user.uid),
      { displayName: user.displayName ?? null, email: user.email ?? null },
      { merge: true },
    ).catch(console.error);

    return onSnapshot(doc(db, "users", user.uid), (snap) => {
      const data = snap.data();
      setTeamIds(data?.teamIds ?? []);
      setLoading(false);
    });
  }, [user]);

  useEffect(() => {
    if (teamIds.length === 0) {
      setTeams([]);
      return;
    }

    const unsubs: (() => void)[] = [];

    for (const teamId of teamIds) {
      let stopAgentSnapshots = () => {};

      const unsubTeam = onSnapshot(doc(db, "teams", teamId), (snap) => {
        if (!snap.exists()) return;

        const data = snap.data();
        const nextAgentIds = Array.isArray(data.agentIds) ? data.agentIds : [];
        firestoreAgentIds.current[teamId] = new Set(nextAgentIds);

        setTeams((prev) => {
          const existing = prev.find((team) => team.id === teamId);
          const updated: Team = {
            id: snap.id,
            name: data.name ?? "",
            createdAt: typeof data.createdAt === "number" ? data.createdAt : Date.now(),
            orgChart: existing?.orgChart ?? [],
            projectIds: Array.isArray(data.projectIds) ? data.projectIds : [],
            agentIds: nextAgentIds,
          };

          const idx = prev.findIndex((team) => team.id === teamId);
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = updated;
            return copy;
          }
          return [...prev, updated];
        });

        stopAgentSnapshots();
        agentCache.current[teamId] = new Map();

        if (nextAgentIds.length === 0) {
          stopAgentSnapshots = onSnapshot(
            collection(db, "teams", teamId, "agents"),
            (legacySnap) => {
              if (legacySnap.empty) {
                setTeams((prev) =>
                  prev.map((team) =>
                    team.id === teamId ? { ...team, orgChart: [], agentIds: [] } : team,
                  ),
                );
                return;
              }

              const legacyAgents = legacySnap.docs.map((agentDoc) => {
                const agent = agentDoc.data() as Record<string, unknown>;
                return normalizeAgent(agent, agentDoc.id);
              });

              agentCache.current[teamId] = new Map(
                legacyAgents.map((agent) => [agent.id, agent]),
              );

              setTeams((prev) =>
                prev.map((team) =>
                  team.id === teamId
                    ? {
                        ...team,
                        agentIds: legacyAgents.map((agent) => agent.id),
                        orgChart: legacyAgents,
                      }
                    : team,
                ),
              );

              const migrateBatch = writeBatch(db);
              for (const agent of legacyAgents) {
                migrateBatch.set(
                  doc(db, "agents", agent.id),
                  {
                    teamId,
                    parentId: agent.parentId,
                    name: agent.name,
                    job: agent.job,
                    description: agent.description,
                    personality: agent.personality,
                  },
                  { merge: true },
                );
              }
              migrateBatch.update(doc(db, "teams", teamId), {
                agentIds: legacyAgents.map((agent) => agent.id),
              });
              migrateBatch.commit().catch(console.error);
            },
          );
          return;
        }

        const chunkUnsubs = chunkIds(nextAgentIds).map((idsChunk) =>
          onSnapshot(
            query(collection(db, "agents"), where(documentId(), "in", idsChunk)),
            (agentSnap) => {
              const cache = agentCache.current[teamId] ?? new Map<string, OrgChartItem>();
              for (const staleId of idsChunk) {
                cache.delete(staleId);
              }

              for (const agentDoc of agentSnap.docs) {
                const agent = agentDoc.data() as Record<string, unknown>;
                cache.set(agentDoc.id, normalizeAgent(agent, agentDoc.id));
              }

              agentCache.current[teamId] = cache;

              setTeams((prev) =>
                prev.map((team) =>
                  team.id === teamId
                    ? {
                        ...team,
                        agentIds: nextAgentIds,
                        orgChart: nextAgentIds
                          .map((agentId) => cache.get(agentId))
                          .filter((item): item is OrgChartItem => Boolean(item)),
                      }
                    : team,
                ),
              );
            },
          ),
        );

        stopAgentSnapshots = () => chunkUnsubs.forEach((unsubscribe) => unsubscribe());
      });

      unsubs.push(() => {
        stopAgentSnapshots();
        unsubTeam();
      });
    }

    setTeams((prev) => prev.filter((team) => teamIds.includes(team.id)));

    return () => unsubs.forEach((unsubscribe) => unsubscribe());
  }, [teamIds]);

  useEffect(() => {
    if (activeTeamId === null && teams.length > 0) {
      setActiveTeamId(teams[0].id);
    }
  }, [activeTeamId, teams]);

  useEffect(() => {
    const activeTeam = teams.find((team) => team.id === activeTeamId);
    const projectIds = activeTeam?.projectIds ?? [];

    if (projectIds.length === 0) {
      setProjects([]);
      return;
    }

    const unsubs = projectIds.map((projectId) =>
      onSnapshot(doc(db, "projects", projectId), (snap) => {
        if (!snap.exists()) return;

        const data = snap.data();
        const rawStatus = data.analysisStatus;
        const analysisStatus: ProjectAnalysisStatus =
          rawStatus === "running" || rawStatus === "done" || rawStatus === "error"
            ? rawStatus
            : "idle";

        const project: Project = {
          id: snap.id,
          name: data.name ?? "",
          description:
            typeof data.description === "string"
              ? data.description
              : typeof data.desc === "string"
                ? data.desc
                : "",
          projectType:
            typeof data.projectType === "string"
              ? data.projectType
              : typeof data.type === "string"
                ? data.type
                : "",
          createdAt: typeof data.createdAt === "number" ? data.createdAt : Date.now(),
          parcelDefinition: normalizeProjectParcel(data.parcelDefinition),
          attachments: normalizeProjectAttachments(data.attachments),
          analysisStatus,
          analysisUpToDate: data.analysisUpToDate !== false,
        };

        setProjects((prev) => {
          const idx = prev.findIndex((item) => item.id === projectId);
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = project;
            return copy;
          }
          return [...prev, project];
        });
      }),
    );

    setProjects((prev) => prev.filter((project) => projectIds.includes(project.id)));

    return () => unsubs.forEach((unsubscribe) => unsubscribe());
  }, [activeTeamId, teams]);

  const selectTeam = useCallback((id: string) => {
    setActiveTeamId(id);
  }, []);

  const setActiveTab = useCallback(
    (tab: StudioTab) => {
      router.push(getStudioTabHref(tab));
    },
    [router],
  );

  const setOptimizeCanvasEmbeds = useCallback((value: boolean) => {
    setSettings((current) => {
      if (current.optimizeCanvasEmbeds === value) return current;
      return {
        ...current,
        optimizeCanvasEmbeds: value,
      };
    });
  }, []);

  const selectProject = useCallback((id: string | null) => {
    setSelectedProjectIdState(id);
  }, []);

  const addProject = useCallback(
    async ({ name, description, projectType, parcelDefinition, attachments }: NewProjectInput) => {
      if (!user || !activeTeamId) return;

      const serializedParcelDefinition = serializeProjectParcel(parcelDefinition);
      const siteCoordinates = parcelDefinition ? serializeProjectCoordinates(parcelDefinition.coordinates) : null;
      const siteCenter = parcelDefinition?.center ?? null;
      const analysisRadius = parcelDefinition?.analysisRadiusMeters ?? null;

      const projectRef = await addDoc(collection(db, "projects"), {
        name,
        desc: description,
        description,
        type: projectType,
        projectType,
        createdAt: Date.now(),
        site_coordinates: siteCoordinates,
        site_center: siteCenter,
        analysis_radius: analysisRadius,
        parcelDefinition: serializedParcelDefinition,
        attachments: [],
        analysisUpToDate: true,
      });

      const uploadedAttachments = await Promise.all(
        attachments.map(async (file) => {
          const timestamp = Date.now();
          const storagePath = `projects/${projectRef.id}/${timestamp}-${file.name}`;
          const attachmentRef = ref(storage, storagePath);
          await uploadBytes(attachmentRef, file, { contentType: file.type || undefined });
          const url = await getDownloadURL(attachmentRef);
          return {
            name: file.name,
            contentType: file.type,
            size: file.size,
            url,
            storagePath,
          } satisfies ProjectAttachment;
        }),
      );

      if (uploadedAttachments.length > 0) {
        await updateDoc(projectRef, {
          attachments: uploadedAttachments,
        });
      }

      await seedProjectWorkspace(projectRef.id, user.uid);

      // Fire analysis in background — status is written to Firestore by the backend.
      runInitialProjectAnalysis({
        projectId: projectRef.id,
        name,
        description,
        projectType,
        parcelDefinition,
      }).catch((error) => {
        console.error("Failed to run initial project analysis", error);
      });

      await updateDoc(doc(db, "teams", activeTeamId), {
        projectIds: arrayUnion(projectRef.id),
      });
    },
    [activeTeamId, user],
  );

  const updateProject = useCallback(
    async ({
      projectId,
      name,
      description,
      projectType,
      parcelDefinition,
      attachmentsToAdd = [],
      attachmentsToRemove = [],
    }: UpdateProjectInput) => {
      if (!user) return;

      const projectRef = doc(db, "projects", projectId);
      const serializedParcelDefinition = serializeProjectParcel(parcelDefinition);
      const siteCoordinates = parcelDefinition ? serializeProjectCoordinates(parcelDefinition.coordinates) : null;
      const siteCenter = parcelDefinition?.center ?? null;
      const analysisRadius = parcelDefinition?.analysisRadiusMeters ?? null;

      const currentProject = projects.find((project) => project.id === projectId) ?? null;
      const retainedAttachments = (currentProject?.attachments ?? []).filter(
        (attachment) =>
          !attachmentsToRemove.some((candidate) => candidate.storagePath === attachment.storagePath),
      );

      if (attachmentsToRemove.length > 0) {
        await Promise.allSettled(
          attachmentsToRemove.map((attachment) => deleteObject(ref(storage, attachment.storagePath))),
        );
      }

      const uploadedAttachments = await Promise.all(
        attachmentsToAdd.map(async (file) => {
          const timestamp = Date.now();
          const storagePath = `projects/${projectId}/${timestamp}-${file.name}`;
          const attachmentRef = ref(storage, storagePath);
          await uploadBytes(attachmentRef, file, { contentType: file.type || undefined });
          const url = await getDownloadURL(attachmentRef);
          return {
            name: file.name,
            contentType: file.type,
            size: file.size,
            url,
            storagePath,
          } satisfies ProjectAttachment;
        }),
      );

      await updateDoc(projectRef, {
        name,
        desc: description,
        description,
        type: projectType,
        projectType,
        site_coordinates: siteCoordinates,
        site_center: siteCenter,
        analysis_radius: analysisRadius,
        parcelDefinition: serializedParcelDefinition,
        attachments: [...retainedAttachments, ...uploadedAttachments],
        updatedAt: Date.now(),
        analysisUpToDate: false,
      });
    },
    [projects, user],
  );

  const runAnalysis = useCallback(
    (projectId: string) => {
      const project = projects.find((p) => p.id === projectId);
      if (!project) return;

      runInitialProjectAnalysis({
        projectId,
        name: project.name,
        description: project.description,
        projectType: project.projectType,
        parcelDefinition: project.parcelDefinition,
      }).catch((error) => {
        console.error("Failed to run project analysis", error);
      });
    },
    [projects],
  );

  const addTeam = useCallback(
    async (name: string) => {
      if (!user) return;

      const teamRef = await addDoc(collection(db, "teams"), {
        name,
        createdAt: Date.now(),
        projectIds: [],
        agentIds: [],
      });

      const managerRef = doc(collection(db, "agents"));
      const defaultManager = createDefaultManagerNode(jobs);
      await setDoc(managerRef, {
        teamId: teamRef.id,
        parentId: null,
        name: defaultManager.name,
        job: defaultManager.job,
        description: defaultManager.description,
        personality: defaultManager.personality,
      });

      await updateDoc(doc(db, "teams", teamRef.id), {
        agentIds: arrayUnion(managerRef.id),
      });

      await setDoc(
        doc(db, "users", user.uid),
        { teamIds: arrayUnion(teamRef.id) },
        { merge: true },
      );

      setActiveTeamId(teamRef.id);
    },
    [jobs, user],
  );

  const updateTeamOrgChart = useCallback((teamId: string, items: OrgChartItem[]) => {
    setTeams((prev) =>
      prev.map((team) =>
        team.id === teamId ? { ...team, orgChart: items, agentIds: items.map((item) => item.id) } : team,
      ),
    );

    if (writeTimer.current) clearTimeout(writeTimer.current);

    writeTimer.current = setTimeout(() => {
      firestoreAgentIds.current[teamId] = new Set(items.map((item) => item.id));

      const batch = writeBatch(db);

      for (const item of items) {
        batch.set(
          doc(db, "agents", item.id),
          {
            teamId,
            parentId: item.parentId,
            name: item.name,
            job: item.job,
            description: item.description,
            personality: item.personality,
          },
          { merge: true },
        );
      }

      batch.update(doc(db, "teams", teamId), {
        agentIds: items.map((item) => item.id),
      });

      batch.commit().catch(console.error);
    }, 500);
  }, []);

  const selectedProjectId =
    selectedProjectIdState && projects.some((project) => project.id === selectedProjectIdState)
      ? selectedProjectIdState
      : projects[0]?.id ?? null;
  const activeProject = selectedProjectId
    ? projects.find((project) => project.id === selectedProjectId) ?? null
    : null;

  return (
    <StudioContext.Provider
      value={{
        loading,
        activeTab,
        setActiveTab,
        settings,
        setOptimizeCanvasEmbeds,
        jobs,
        personalities,
        projects,
        activeProject,
        selectedProjectId,
        selectProject,
        addProject,
        updateProject,
        runAnalysis,
        teams,
        activeTeamId,
        selectTeam,
        addTeam,
        updateTeamOrgChart,
        notifications,
        dismissNotification,
      }}
    >
      {children}
    </StudioContext.Provider>
  );
}

export function useStudio() {
  const ctx = useContext(StudioContext);
  if (!ctx) throw new Error("useStudio must be used within StudioProvider");
  return ctx;
}
