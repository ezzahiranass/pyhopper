"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  addDoc,
  collection,
  deleteDoc,
  doc,
  getDocs,
  onSnapshot,
  updateDoc,
  writeBatch,
} from "firebase/firestore";
import { useAuth } from "@/components/auth-provider";
import { db } from "@/lib/firebase";
import type {
  WorkspaceArea,
  WorkspaceArtifactMap,
  WorkspaceSubdomain,
} from "@/components/studio/types";
import {
  AREA_INSET,
  FRAME_BOTTOM_PADDING,
  FRAME_CONTENT_OFFSET_X,
  FRAME_CONTENT_OFFSET_Y,
  FRAME_RIGHT_PADDING,
  WORKSPACE_SEED_TEMPLATE,
  buildSeededWorkspaceHierarchy,
} from "@/components/workspace/workspace-data";

type WorkspaceMetadataArea = Omit<WorkspaceArea, "order" | "frameX" | "frameY" | "frameW" | "frameH" | "subdomains"> & {
  subdomains: WorkspaceMetadataSubdomain[];
};

type WorkspaceMetadataSubdomain = Omit<WorkspaceSubdomain, "order" | "x" | "y" | "w" | "h">;

type WorkspaceLocalSubdomainLayout = Pick<WorkspaceSubdomain, "x" | "y" | "w" | "h">;
type WorkspaceLocalAreaFrame = Pick<WorkspaceArea, "frameX" | "frameY" | "frameW" | "frameH">;

type WorkspaceLocalLayoutCache = {
  areaOrder: string[];
  areaFrames: Record<string, WorkspaceLocalAreaFrame>;
  subdomainOrder: Record<string, string[]>;
  subdomains: Record<string, WorkspaceLocalSubdomainLayout>;
};

const LOCAL_STORAGE_PREFIX = "workspace-layout";
const FALLBACK_SUBDOMAIN_WIDTH = 176;
const FALLBACK_SUBDOMAIN_HEIGHT = 120;
const FALLBACK_COLUMN_GAP = 28;
const FALLBACK_ROW_GAP = 28;
const FALLBACK_COLUMN_WIDTH = 208;
const FALLBACK_SECTION_STRIDE_X = 420;
const FALLBACK_SECTION_STRIDE_Y = 320;
const FALLBACK_AREA_WIDTH = 320;
const FALLBACK_AREA_HEIGHT = 220;
const SEEDED_AREA_SLUGS = new Set(WORKSPACE_SEED_TEMPLATE.map((area) => area.slug));
const SEEDED_SUBDOMAIN_SLUGS = new Map(
  WORKSPACE_SEED_TEMPLATE.map((area) => [area.slug, new Set(area.subdomains.map((subdomain) => subdomain.slug))]),
);

function isSeededAreaSlug(slug: string) {
  return SEEDED_AREA_SLUGS.has(slug);
}

function isSeededSubdomainSlug(areaSlug: string, subdomainSlug: string) {
  return SEEDED_SUBDOMAIN_SLUGS.get(areaSlug)?.has(subdomainSlug) ?? false;
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

function normalizeCoordinates(value: unknown): [number, number][][] | null {
  if (!Array.isArray(value)) return null;

  const rings = value
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

  return rings.length > 0 ? rings : null;
}

function normalizeArtifacts(value: unknown): WorkspaceArtifactMap {
  if (!value || typeof value !== "object") return {};

  const normalized: WorkspaceArtifactMap = {};

  for (const [artifactId, rawArtifact] of Object.entries(value as Record<string, unknown>)) {
    if (!rawArtifact || typeof rawArtifact !== "object") continue;
    const artifact = rawArtifact as {
      type?: unknown;
      label?: unknown;
      value?: unknown;
    };

    const type = typeof artifact.type === "string" ? artifact.type : "";
    const label = typeof artifact.label === "string" ? artifact.label : artifactId;

    if (type === "text") {
      normalized[artifactId] = {
        type: "text",
        label,
        value: typeof artifact.value === "string" ? artifact.value : "",
      };
      continue;
    }

    if (type === "geolocation" && artifact.value && typeof artifact.value === "object") {
      const geo = artifact.value as {
        coordinates?: unknown;
        center?: unknown;
        analysisRadiusMeters?: unknown;
        overlaysGeojson?: unknown;
        mapStyle?: unknown;
      };
      const rawStyle = geo.mapStyle && typeof geo.mapStyle === "object" ? geo.mapStyle as Record<string, unknown> : null;
      normalized[artifactId] = {
        type: "geolocation",
        label,
        value: {
          coordinates: normalizeCoordinates(geo.coordinates),
          center: normalizeLngLatPoint(geo.center),
          analysisRadiusMeters:
            typeof geo.analysisRadiusMeters === "number"
              ? geo.analysisRadiusMeters
              : Number(geo.analysisRadiusMeters) || null,
          overlaysGeojson: typeof geo.overlaysGeojson === "string" ? geo.overlaysGeojson : undefined,
          mapStyle: rawStyle ? {
            basemapSaturation: typeof rawStyle.basemapSaturation === "number" ? rawStyle.basemapSaturation : undefined,
            basemapContrast: typeof rawStyle.basemapContrast === "number" ? rawStyle.basemapContrast : undefined,
            basemapBrightnessMin: typeof rawStyle.basemapBrightnessMin === "number" ? rawStyle.basemapBrightnessMin : undefined,
            basemapBrightnessMax: typeof rawStyle.basemapBrightnessMax === "number" ? rawStyle.basemapBrightnessMax : undefined,
            showLabels: typeof rawStyle.showLabels === "boolean" ? rawStyle.showLabels : undefined,
            showIcons: typeof rawStyle.showIcons === "boolean" ? rawStyle.showIcons : undefined,
            backgroundColor: typeof rawStyle.backgroundColor === "string" ? rawStyle.backgroundColor : undefined,
          } : undefined,
        },
      };
      continue;
    }

    if (type === "image" && artifact.value && typeof artifact.value === "object") {
      const image = artifact.value as { url?: unknown; alt?: unknown };
      const url = typeof image.url === "string" ? image.url : "";
      if (!url) continue;

      normalized[artifactId] = {
        type: "image",
        label,
        value: {
          url,
          alt: typeof image.alt === "string" ? image.alt : undefined,
        },
      };
      continue;
    }

    if (type === "model" && artifact.value && typeof artifact.value === "object") {
      const model = artifact.value as { url?: unknown; storagePath?: unknown; format?: unknown };
      const url = typeof model.url === "string" ? model.url : "";
      if (!url) continue;

      normalized[artifactId] = {
        type: "model",
        label,
        value: {
          url,
          storagePath: typeof model.storagePath === "string" ? model.storagePath : undefined,
          format: typeof model.format === "string" ? model.format : undefined,
        },
      };
    }
  }

  return normalized;
}

function getLocalStorageKey(projectId: string) {
  return `${LOCAL_STORAGE_PREFIX}:${projectId}`;
}

function isLocalStorageAvailable() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function readLocalLayout(projectId: string): WorkspaceLocalLayoutCache | null {
  if (!isLocalStorageAvailable()) return null;

  try {
    const raw = window.localStorage.getItem(getLocalStorageKey(projectId));
    if (!raw) return null;

    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;

    return {
      areaOrder: Array.isArray(parsed.areaOrder)
        ? (parsed.areaOrder as unknown[]).filter((value): value is string => typeof value === "string")
        : [],
      areaFrames:
        parsed.areaFrames && typeof parsed.areaFrames === "object"
          ? Object.fromEntries(
              Object.entries(parsed.areaFrames as Record<string, unknown>).flatMap(([areaId, value]) => {
                if (!value || typeof value !== "object") return [];

                const candidate = value as Partial<WorkspaceLocalAreaFrame>;
                if (
                  typeof candidate.frameX !== "number" ||
                  typeof candidate.frameY !== "number" ||
                  typeof candidate.frameW !== "number" ||
                  typeof candidate.frameH !== "number"
                ) {
                  return [];
                }

                return [[areaId, {
                  frameX: candidate.frameX,
                  frameY: candidate.frameY,
                  frameW: candidate.frameW,
                  frameH: candidate.frameH,
                } satisfies WorkspaceLocalAreaFrame]];
              }),
            )
          : {},
      subdomainOrder:
        parsed.subdomainOrder && typeof parsed.subdomainOrder === "object"
          ? Object.fromEntries(
              Object.entries(parsed.subdomainOrder as Record<string, unknown>).map(([areaId, value]) => [
                areaId,
                Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === "string") : [],
              ]),
            )
          : {},
      subdomains:
        parsed.subdomains && typeof parsed.subdomains === "object"
          ? Object.fromEntries(
              Object.entries(parsed.subdomains as Record<string, unknown>).flatMap(([subdomainId, value]) => {
                if (!value || typeof value !== "object") return [];

                const candidate = value as Partial<WorkspaceLocalSubdomainLayout>;
                if (
                  typeof candidate.x !== "number" ||
                  typeof candidate.y !== "number" ||
                  typeof candidate.w !== "number" ||
                  typeof candidate.h !== "number"
                ) {
                  return [];
                }

                return [[subdomainId, {
                  x: candidate.x,
                  y: candidate.y,
                  w: candidate.w,
                  h: candidate.h,
                } satisfies WorkspaceLocalSubdomainLayout]];
              }),
            )
          : {},
    };
  } catch {
    return null;
  }
}

function writeLocalLayout(projectId: string, layout: WorkspaceLocalLayoutCache) {
  if (!isLocalStorageAvailable()) return;
  window.localStorage.setItem(getLocalStorageKey(projectId), JSON.stringify(layout));
}

function mergeOrderedIds(storedIds: string[], defaults: string[], availableIds: Set<string>) {
  const merged: string[] = [];
  const seen = new Set<string>();

  for (const id of [...storedIds, ...defaults]) {
    if (!availableIds.has(id) || seen.has(id)) continue;
    seen.add(id);
    merged.push(id);
  }

  return merged;
}

function compareStringArrays(left: string[], right: string[]) {
  if (left.length !== right.length) return false;
  return left.every((value, index) => value === right[index]);
}

function compareLayouts(
  left: WorkspaceLocalSubdomainLayout | undefined,
  right: WorkspaceLocalSubdomainLayout | undefined,
) {
  if (!left || !right) return left === right;
  return left.x === right.x && left.y === right.y && left.w === right.w && left.h === right.h;
}

function compareLocalCaches(left: WorkspaceLocalLayoutCache, right: WorkspaceLocalLayoutCache) {
  if (!compareStringArrays(left.areaOrder, right.areaOrder)) return false;

  const leftFrameIds = Object.keys(left.areaFrames).sort();
  const rightFrameIds = Object.keys(right.areaFrames).sort();
  if (!compareStringArrays(leftFrameIds, rightFrameIds)) return false;

  for (const areaId of leftFrameIds) {
    const leftFrame = left.areaFrames[areaId];
    const rightFrame = right.areaFrames[areaId];
    if (
      !rightFrame ||
      leftFrame.frameX !== rightFrame.frameX ||
      leftFrame.frameY !== rightFrame.frameY ||
      leftFrame.frameW !== rightFrame.frameW ||
      leftFrame.frameH !== rightFrame.frameH
    ) {
      return false;
    }
  }

  const leftAreaIds = Object.keys(left.subdomainOrder).sort();
  const rightAreaIds = Object.keys(right.subdomainOrder).sort();
  if (!compareStringArrays(leftAreaIds, rightAreaIds)) return false;

  for (const areaId of leftAreaIds) {
    if (!compareStringArrays(left.subdomainOrder[areaId] ?? [], right.subdomainOrder[areaId] ?? [])) {
      return false;
    }
  }

  const leftSubdomainIds = Object.keys(left.subdomains).sort();
  const rightSubdomainIds = Object.keys(right.subdomains).sort();
  if (!compareStringArrays(leftSubdomainIds, rightSubdomainIds)) return false;

  for (const subdomainId of leftSubdomainIds) {
    if (!compareLayouts(left.subdomains[subdomainId], right.subdomains[subdomainId])) {
      return false;
    }
  }

  return true;
}

function buildFallbackLayout(areaIndex: number, subdomainIndex: number): WorkspaceLocalSubdomainLayout {
  const column = subdomainIndex % 2;
  const row = Math.floor(subdomainIndex / 2);

  return {
    x: areaIndex * FALLBACK_SECTION_STRIDE_X + column * (FALLBACK_COLUMN_WIDTH + FALLBACK_COLUMN_GAP),
    y: areaIndex * FALLBACK_SECTION_STRIDE_Y + row * (FALLBACK_SUBDOMAIN_HEIGHT + FALLBACK_ROW_GAP),
    w: FALLBACK_SUBDOMAIN_WIDTH,
    h: FALLBACK_SUBDOMAIN_HEIGHT,
  };
}

function buildFallbackAreaFrame(areaIndex: number): WorkspaceLocalAreaFrame {
  return {
    frameX: areaIndex * FALLBACK_SECTION_STRIDE_X - 38,
    frameY: areaIndex * 72,
    frameW: FALLBACK_AREA_WIDTH,
    frameH: FALLBACK_AREA_HEIGHT,
  };
}

function buildNewSubdomainLayout(
  areaFrame: WorkspaceLocalAreaFrame | undefined,
  siblingLayouts: WorkspaceLocalSubdomainLayout[],
): WorkspaceLocalSubdomainLayout {
  if (siblingLayouts.length === 0) {
    return {
      x: (areaFrame?.frameX ?? 0) + FRAME_CONTENT_OFFSET_X + AREA_INSET,
      y: (areaFrame?.frameY ?? 0) + FRAME_CONTENT_OFFSET_Y + AREA_INSET,
      w: FALLBACK_SUBDOMAIN_WIDTH,
      h: FALLBACK_SUBDOMAIN_HEIGHT,
    };
  }

  const rightMost = siblingLayouts.reduce((best, layout) => {
    if (!best) return layout;
    return layout.x + layout.w > best.x + best.w ? layout : best;
  }, siblingLayouts[0]);

  return {
    x: rightMost.x + rightMost.w + FALLBACK_COLUMN_GAP,
    y: rightMost.y,
    w: FALLBACK_SUBDOMAIN_WIDTH,
    h: FALLBACK_SUBDOMAIN_HEIGHT,
  };
}

function deriveAreaFrameFromLayouts(
  layouts: WorkspaceLocalSubdomainLayout[],
  fallbackFrame: WorkspaceLocalAreaFrame | undefined,
): WorkspaceLocalAreaFrame {
  if (layouts.length === 0) {
    return fallbackFrame ?? buildFallbackAreaFrame(0);
  }

  const minX = Math.min(...layouts.map((layout) => layout.x));
  const minY = Math.min(...layouts.map((layout) => layout.y));
  const maxX = Math.max(...layouts.map((layout) => layout.x + layout.w));
  const maxY = Math.max(...layouts.map((layout) => layout.y + layout.h));
  const frameX = minX - FRAME_CONTENT_OFFSET_X - AREA_INSET;
  const frameY = minY - FRAME_CONTENT_OFFSET_Y - AREA_INSET;

  return {
    frameX,
    frameY,
    frameW: maxX - frameX + AREA_INSET + FRAME_RIGHT_PADDING,
    frameH: maxY - frameY + AREA_INSET + FRAME_BOTTOM_PADDING,
  };
}

function buildDefaultLayout(areas: WorkspaceMetadataArea[]): WorkspaceLocalLayoutCache {
  const areaOrderBySlug = new Map(
    WORKSPACE_SEED_TEMPLATE.map((area, index) => [area.slug, index]),
  );

  const sortedAreas = [...areas].sort((left, right) => {
    const leftSeed = areaOrderBySlug.get(left.slug) ?? Number.MAX_SAFE_INTEGER;
    const rightSeed = areaOrderBySlug.get(right.slug) ?? Number.MAX_SAFE_INTEGER;
    if (leftSeed !== rightSeed) return leftSeed - rightSeed;
    return left.name.localeCompare(right.name);
  });

  const areaOrder = sortedAreas.map((area) => area.id);
  const areaFrames: Record<string, WorkspaceLocalAreaFrame> = {};
  const subdomainOrder: Record<string, string[]> = {};
  const subdomains: Record<string, WorkspaceLocalSubdomainLayout> = {};

  sortedAreas.forEach((area, areaIndex) => {
    areaFrames[area.id] = buildFallbackAreaFrame(areaIndex);
    const subdomainOrderBySlug = new Map(
      (WORKSPACE_SEED_TEMPLATE.find((entry) => entry.slug === area.slug)?.subdomains ?? []).map((subdomain, index) => [
        subdomain.slug,
        index,
      ]),
    );
    const sortedSubdomains = [...area.subdomains].sort((left, right) => {
      const leftSeed = subdomainOrderBySlug.get(left.slug) ?? Number.MAX_SAFE_INTEGER;
      const rightSeed = subdomainOrderBySlug.get(right.slug) ?? Number.MAX_SAFE_INTEGER;
      if (leftSeed !== rightSeed) return leftSeed - rightSeed;
      return left.name.localeCompare(right.name);
    });

    subdomainOrder[area.id] = sortedSubdomains.map((subdomain) => subdomain.id);

    sortedSubdomains.forEach((subdomain, subdomainIndex) => {
      subdomains[subdomain.id] = buildFallbackLayout(areaIndex, subdomainIndex);
    });
  });

  return {
    areaOrder,
    areaFrames,
    subdomainOrder,
    subdomains,
  };
}

function hydrateWorkspace(projectId: string, areas: WorkspaceMetadataArea[]) {
  const defaults = buildDefaultLayout(areas);
  const stored = readLocalLayout(projectId);
  const availableAreaIds = new Set(areas.map((area) => area.id));
  const areaOrder = mergeOrderedIds(stored?.areaOrder ?? [], defaults.areaOrder, availableAreaIds);
  const areasById = new Map(areas.map((area) => [area.id, area]));
  const mergedAreaFrames: Record<string, WorkspaceLocalAreaFrame> = {};
  const mergedSubdomainOrder: Record<string, string[]> = {};
  const mergedSubdomains: Record<string, WorkspaceLocalSubdomainLayout> = {};

  const hydratedAreas = areaOrder.flatMap((areaId, areaOrderIndex) => {
    const area = areasById.get(areaId);
    if (!area) return [];
    const areaFrame = stored?.areaFrames[area.id] ?? defaults.areaFrames[area.id] ?? buildFallbackAreaFrame(areaOrderIndex);
    mergedAreaFrames[area.id] = areaFrame;

    const availableSubdomainIds = new Set(area.subdomains.map((subdomain) => subdomain.id));
    const defaultSubdomainOrder = defaults.subdomainOrder[area.id] ?? [];
    const subdomainOrder = mergeOrderedIds(
      stored?.subdomainOrder[area.id] ?? [],
      defaultSubdomainOrder,
      availableSubdomainIds,
    );

    mergedSubdomainOrder[area.id] = subdomainOrder;

    const subdomainsById = new Map(area.subdomains.map((subdomain) => [subdomain.id, subdomain]));
    const hydratedSubdomains = subdomainOrder.flatMap((subdomainId, subdomainOrderIndex) => {
      const subdomain = subdomainsById.get(subdomainId);
      if (!subdomain) return [];

      const defaultLayout = defaults.subdomains[subdomain.id] ?? buildFallbackLayout(areaOrderIndex, subdomainOrderIndex);
      const storedLayout = stored?.subdomains[subdomain.id];
      const layout = storedLayout ?? defaultLayout;

      mergedSubdomains[subdomain.id] = layout;

      return [{
        ...subdomain,
        order: subdomainOrderIndex,
        x: layout.x,
        y: layout.y,
        w: layout.w,
        h: layout.h,
      } satisfies WorkspaceSubdomain];
    });

    return [{
      ...area,
      order: areaOrderIndex,
      frameX: areaFrame.frameX,
      frameY: areaFrame.frameY,
      frameW: areaFrame.frameW,
      frameH: areaFrame.frameH,
      subdomains: hydratedSubdomains,
    } satisfies WorkspaceArea];
  });

  const mergedLayout: WorkspaceLocalLayoutCache = {
    areaOrder,
    areaFrames: mergedAreaFrames,
    subdomainOrder: mergedSubdomainOrder,
    subdomains: mergedSubdomains,
  };

  if (!stored || !compareLocalCaches(stored, mergedLayout)) {
    writeLocalLayout(projectId, mergedLayout);
  }

  return hydratedAreas;
}

function updateStoredLayout(
  projectId: string,
  updater: (current: WorkspaceLocalLayoutCache) => WorkspaceLocalLayoutCache,
) {
  const current = readLocalLayout(projectId) ?? {
    areaOrder: [],
    areaFrames: {},
    subdomainOrder: {},
    subdomains: {},
  };
  const next = updater(current);
  writeLocalLayout(projectId, next);
  return next;
}

function slugifyWorkspaceValue(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || `item-${Date.now()}`;
}

export async function seedProjectWorkspace(projectId: string, userId: string | null) {
  const timestamp = Date.now();
  const batch = writeBatch(db);

  for (const area of buildSeededWorkspaceHierarchy()) {
    const areaRef = doc(collection(db, "projects", projectId, "workspace"));
    batch.set(areaRef, {
      slug: area.slug,
      name: area.name,
      description: area.description,
      type: area.type,
      isLocked: true,
      createdBy: userId,
      createdAt: timestamp,
    });

    for (const subdomain of area.subdomains) {
      const subdomainRef = doc(collection(db, "projects", projectId, "workspace", areaRef.id, "subdomains"));
      batch.set(subdomainRef, {
        slug: subdomain.slug,
        name: subdomain.name,
        description: subdomain.description,
        type: subdomain.type,
        isLocked: true,
        createdBy: userId,
        createdAt: timestamp,
      });
    }
  }

  await batch.commit();
}

export function useProjectWorkspace(projectId: string | null) {
  const { user } = useAuth();
  const [snapshotState, setSnapshotState] = useState<{
    projectId: string | null;
    areas: WorkspaceArea[];
  }>({
    projectId: null,
    areas: [],
  });
  const areasRef = useRef<WorkspaceMetadataArea[]>([]);
  const subdomainsRef = useRef<Record<string, WorkspaceMetadataSubdomain[]>>({});
  const loadedSubdomainAreaIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!projectId) return;
    const subdomainUnsubs: Array<() => void> = [];
    loadedSubdomainAreaIdsRef.current = new Set();

    const publish = () => {
      const currentAreaIds = areasRef.current.map((area) => area.id);
      if (currentAreaIds.length > 0) {
        const allSubdomainsLoaded = currentAreaIds.every((areaId) => loadedSubdomainAreaIdsRef.current.has(areaId));
        if (!allSubdomainsLoaded) return;
      }

      const areas = areasRef.current.map((area) => ({
        ...area,
        subdomains: subdomainsRef.current[area.id] ?? [],
      }));

      setSnapshotState({
        projectId,
        areas: hydrateWorkspace(projectId, areas),
      });
    };

    const unsubscribe = onSnapshot(
      collection(db, "projects", projectId, "workspace"),
      (snapshot) => {
        for (const stop of subdomainUnsubs.splice(0, subdomainUnsubs.length)) {
          stop();
        }

        areasRef.current = snapshot.docs.map((areaDoc) => {
          const data = areaDoc.data();
          const slug = typeof data.slug === "string" ? data.slug : areaDoc.id;
          return {
            id: areaDoc.id,
            slug,
            name: typeof data.name === "string" ? data.name : "",
            description: typeof data.description === "string" ? data.description : "",
            type: typeof data.type === "string" ? data.type : "",
            isLocked: typeof data.isLocked === "boolean" ? data.isLocked : isSeededAreaSlug(slug),
            createdBy: typeof data.createdBy === "string" ? data.createdBy : null,
            createdAt: typeof data.createdAt === "number" ? data.createdAt : Date.now(),
            subdomains: subdomainsRef.current[areaDoc.id] ?? [],
          } satisfies WorkspaceMetadataArea;
        });

        const currentAreaIds = new Set(areasRef.current.map((area) => area.id));
        loadedSubdomainAreaIdsRef.current = new Set(
          [...loadedSubdomainAreaIdsRef.current].filter((areaId) => currentAreaIds.has(areaId)),
        );
        for (const areaId of Object.keys(subdomainsRef.current)) {
          if (!currentAreaIds.has(areaId)) {
            delete subdomainsRef.current[areaId];
          }
        }

        for (const area of areasRef.current) {
          subdomainUnsubs.push(
            onSnapshot(
              collection(db, "projects", projectId, "workspace", area.id, "subdomains"),
              (subSnapshot) => {
                subdomainsRef.current[area.id] = subSnapshot.docs.map((subDoc) => {
                  const data = subDoc.data();
                  const slug = typeof data.slug === "string" ? data.slug : subDoc.id;
                  return {
                    id: subDoc.id,
                    areaId: area.id,
                    slug,
                    name: typeof data.name === "string" ? data.name : "",
                    description: typeof data.description === "string" ? data.description : "",
                    type: typeof data.type === "string" ? data.type : "",
                    content: typeof data.content === "string" ? data.content : null,
                    artifacts: normalizeArtifacts(data.artifacts),
                    isLocked: typeof data.isLocked === "boolean" ? data.isLocked : isSeededSubdomainSlug(area.slug, slug),
                    createdBy: typeof data.createdBy === "string" ? data.createdBy : null,
                    createdAt: typeof data.createdAt === "number" ? data.createdAt : Date.now(),
                  } satisfies WorkspaceMetadataSubdomain;
                });
                loadedSubdomainAreaIdsRef.current = new Set(loadedSubdomainAreaIdsRef.current).add(area.id);

                publish();
              },
            ),
          );
        }

        publish();
      },
    );

    return () => {
      unsubscribe();
      for (const stop of subdomainUnsubs) {
        stop();
      }
    };
  }, [projectId]);

  const areas = useMemo(
    () => (projectId && snapshotState.projectId === projectId ? snapshotState.areas : []),
    [projectId, snapshotState.areas, snapshotState.projectId],
  );
  const loading = useMemo(
    () => Boolean(projectId) && snapshotState.projectId !== projectId,
    [projectId, snapshotState.projectId],
  );

  return useMemo(() => ({
    loading,
    areas,
    async persistSubdomainLayout(areaId: string, subdomainId: string, layout: Pick<WorkspaceSubdomain, "x" | "y" | "w" | "h">) {
      if (!projectId) return;

      const nextAreas = areas.map((area) =>
        area.id === areaId
          ? {
              ...area,
              subdomains: area.subdomains.map((subdomain) =>
                subdomain.id === subdomainId ? { ...subdomain, ...layout } : subdomain,
              ),
            }
          : area,
      );
      const nextArea = nextAreas.find((area) => area.id === areaId);
      const nextAreaFrame = deriveAreaFrameFromLayouts(
        (nextArea?.subdomains ?? []).map((subdomain) => ({
          x: subdomain.x,
          y: subdomain.y,
          w: subdomain.w,
          h: subdomain.h,
        })),
        nextArea
          ? {
              frameX: nextArea.frameX,
              frameY: nextArea.frameY,
              frameW: nextArea.frameW,
              frameH: nextArea.frameH,
            }
          : undefined,
      );

      updateStoredLayout(projectId, (current) => ({
        areaOrder: current.areaOrder,
        areaFrames: {
          ...current.areaFrames,
          [areaId]: nextAreaFrame,
        },
        subdomainOrder: current.subdomainOrder,
        subdomains: {
          ...current.subdomains,
          [subdomainId]: layout,
        },
      }));

      setSnapshotState({
        projectId,
        areas: hydrateWorkspace(projectId, nextAreas),
      });
    },
    async persistAreaDelta(areaId: string, updates: Array<{ id: string; x: number; y: number }>) {
      if (!projectId || updates.length === 0) return;

      const updateMap = new Map(updates.map((entry) => [entry.id, entry]));
      const nextAreas = areas.map((area) =>
        area.id === areaId
          ? {
              ...area,
              subdomains: area.subdomains.map((subdomain) => {
                const update = updateMap.get(subdomain.id);
                return update
                  ? {
                      ...subdomain,
                      x: update.x,
                      y: update.y,
                    }
                  : subdomain;
              }),
            }
          : area,
      );
      const nextArea = nextAreas.find((area) => area.id === areaId);
      const nextAreaFrame = deriveAreaFrameFromLayouts(
        (nextArea?.subdomains ?? []).map((subdomain) => ({
          x: subdomain.x,
          y: subdomain.y,
          w: subdomain.w,
          h: subdomain.h,
        })),
        nextArea
          ? {
              frameX: nextArea.frameX,
              frameY: nextArea.frameY,
              frameW: nextArea.frameW,
              frameH: nextArea.frameH,
            }
          : undefined,
      );

      updateStoredLayout(projectId, (current) => ({
        areaOrder: current.areaOrder,
        areaFrames: {
          ...current.areaFrames,
          [areaId]: nextAreaFrame,
        },
        subdomainOrder: current.subdomainOrder,
        subdomains: {
          ...current.subdomains,
          ...Object.fromEntries(
            updates.map((update) => [
              update.id,
              {
                ...(current.subdomains[update.id] ?? { x: update.x, y: update.y, w: FALLBACK_SUBDOMAIN_WIDTH, h: FALLBACK_SUBDOMAIN_HEIGHT }),
                x: update.x,
                y: update.y,
              },
            ]),
          ),
        },
      }));

      setSnapshotState({
        projectId,
        areas: hydrateWorkspace(projectId, nextAreas),
      });
    },
    async persistAreaFrame(areaId: string, frame: WorkspaceLocalAreaFrame) {
      if (!projectId) return;

      const nextAreas = areas.map((area) =>
        area.id === areaId
          ? {
              ...area,
              ...frame,
            }
          : area,
      );

      updateStoredLayout(projectId, (current) => ({
        areaOrder: current.areaOrder,
        areaFrames: {
          ...current.areaFrames,
          [areaId]: frame,
        },
        subdomainOrder: current.subdomainOrder,
        subdomains: current.subdomains,
      }));

      setSnapshotState({
        projectId,
        areas: hydrateWorkspace(projectId, nextAreas),
      });
    },
    async createArea(input: { name: string; description: string }) {
      if (!projectId) return null;

      const areaRef = await addDoc(collection(db, "projects", projectId, "workspace"), {
        slug: slugifyWorkspaceValue(input.name),
        name: input.name,
        description: input.description,
        type: "Canvas",
        isLocked: false,
        createdBy: user?.uid ?? null,
        createdAt: Date.now(),
      });

      updateStoredLayout(projectId, (current) => {
        const nextAreaOrder = current.areaOrder.includes(areaRef.id)
          ? current.areaOrder
          : [...current.areaOrder, areaRef.id];
        const nextIndex = nextAreaOrder.indexOf(areaRef.id);

        return {
          areaOrder: nextAreaOrder,
          areaFrames: {
            ...current.areaFrames,
            [areaRef.id]: current.areaFrames[areaRef.id] ?? buildFallbackAreaFrame(nextIndex),
          },
          subdomainOrder: current.subdomainOrder,
          subdomains: current.subdomains,
        };
      });

      return areaRef.id;
    },
    async createSubdomain(areaId: string, input: { name: string; description: string }) {
      if (!projectId) return;

      const subdomainRef = await addDoc(collection(db, "projects", projectId, "workspace", areaId, "subdomains"), {
        slug: slugifyWorkspaceValue(input.name),
        name: input.name,
        description: input.description,
        type: "subdomain",
        isLocked: false,
        createdBy: user?.uid ?? null,
        createdAt: Date.now(),
      });

      updateStoredLayout(projectId, (current) => ({
        areaOrder: current.areaOrder,
        areaFrames: current.areaFrames,
        subdomainOrder: {
          ...current.subdomainOrder,
          [areaId]: [...(current.subdomainOrder[areaId] ?? []), subdomainRef.id],
        },
        subdomains: {
          ...current.subdomains,
          [subdomainRef.id]: buildNewSubdomainLayout(
            current.areaFrames[areaId],
            (current.subdomainOrder[areaId] ?? [])
              .map((id) => current.subdomains[id])
              .filter((layout): layout is WorkspaceLocalSubdomainLayout => Boolean(layout)),
          ),
        },
      }));

      return subdomainRef.id;
    },
    async updateAreaMetadata(areaId: string, input: { name: string; description: string }) {
      if (!projectId) return;
      const area = areas.find((entry) => entry.id === areaId);
      if (area?.isLocked) return;

      await updateDoc(doc(db, "projects", projectId, "workspace", areaId), {
        slug: slugifyWorkspaceValue(input.name),
        name: input.name,
        description: input.description,
      });
    },
    async updateSubdomainMetadata(areaId: string, subdomainId: string, input: { name: string; description: string }) {
      if (!projectId) return;
      const area = areas.find((entry) => entry.id === areaId);
      const subdomain = area?.subdomains.find((entry) => entry.id === subdomainId);
      if (subdomain?.isLocked) return;

      await updateDoc(doc(db, "projects", projectId, "workspace", areaId, "subdomains", subdomainId), {
        slug: slugifyWorkspaceValue(input.name),
        name: input.name,
        description: input.description,
      });
    },
    async deleteArea(areaId: string) {
      if (!projectId) return;
      const area = areas.find((entry) => entry.id === areaId);
      if (area?.isLocked) return;

      const subdomainsSnapshot = await getDocs(collection(db, "projects", projectId, "workspace", areaId, "subdomains"));
      const batch = writeBatch(db);
      for (const subdomainDoc of subdomainsSnapshot.docs) {
        batch.delete(subdomainDoc.ref);
      }
      batch.delete(doc(db, "projects", projectId, "workspace", areaId));
      await batch.commit();

      updateStoredLayout(projectId, (current) => {
        const nextFrames = { ...current.areaFrames };
        delete nextFrames[areaId];

        const nextSubdomainOrder = { ...current.subdomainOrder };
        const removedSubdomainIds = nextSubdomainOrder[areaId] ?? [];
        delete nextSubdomainOrder[areaId];

        const nextSubdomains = { ...current.subdomains };
        for (const subdomainId of removedSubdomainIds) {
          delete nextSubdomains[subdomainId];
        }

        return {
          areaOrder: current.areaOrder.filter((id) => id !== areaId),
          areaFrames: nextFrames,
          subdomainOrder: nextSubdomainOrder,
          subdomains: nextSubdomains,
        };
      });
    },
    async deleteSubdomain(areaId: string, subdomainId: string) {
      if (!projectId) return;
      const area = areas.find((entry) => entry.id === areaId);
      const subdomain = area?.subdomains.find((entry) => entry.id === subdomainId);
      if (subdomain?.isLocked) return;

      await deleteDoc(doc(db, "projects", projectId, "workspace", areaId, "subdomains", subdomainId));

      updateStoredLayout(projectId, (current) => {
        const nextSubdomainOrder = {
          ...current.subdomainOrder,
          [areaId]: (current.subdomainOrder[areaId] ?? []).filter((id) => id !== subdomainId),
        };
        const nextSubdomains = { ...current.subdomains };
        delete nextSubdomains[subdomainId];

        return {
          areaOrder: current.areaOrder,
          areaFrames: current.areaFrames,
          subdomainOrder: nextSubdomainOrder,
          subdomains: nextSubdomains,
        };
      });
    },
  }), [areas, loading, projectId, user?.uid]);
}
