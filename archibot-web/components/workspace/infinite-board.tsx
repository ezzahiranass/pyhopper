"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { Plus, RefreshCw, Sparkles } from "lucide-react";
import { Rnd } from "react-rnd";
import type { OrgChartItem, Project, WorkspaceArea } from "@/components/studio/types";
import {
  AREA_INSET,
  FRAME_BOTTOM_PADDING,
  FRAME_CONTENT_OFFSET_X,
  FRAME_CONTENT_OFFSET_Y,
  FRAME_RIGHT_PADDING,
} from "@/components/workspace/workspace-data";
import {
  PlaceholderCard,
  type WorkspaceSubAreaLayout,
} from "@/components/workspace/placeholder-card";

type Point = { x: number; y: number };
type Viewport = { x: number; y: number; zoom: number };
type CursorPlacement = {
  id: string;
  x: number;
  y: number;
  name: string;
  job: string;
  driftX: number;
  driftY: number;
  duration: number;
  delay: number;
  isTyping: boolean;
  unreadCount: number;
};
type WorldSubAreaLayout = WorkspaceSubAreaLayout & {
  sectionId: string;
};
type SectionFrame = {
  id: string;
  sectionId: string;
  x: number;
  y: number;
  w: number;
  h: number;
};

function clampZoom(value: number) {
  return Math.min(2.4, Math.max(0.35, value));
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

function flattenAreasToWorld(areas: WorkspaceArea[]): WorldSubAreaLayout[] {
  return areas.flatMap((area) =>
    area.subdomains.map((item) => ({
      id: item.id,
      sectionId: area.id,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
    })),
  );
}

function deriveSectionFrame(
  sectionId: string,
  subAreas: WorldSubAreaLayout[],
  fallbackFrame?: Pick<WorkspaceArea, "frameX" | "frameY" | "frameW" | "frameH">,
): SectionFrame | null {
  if (subAreas.length === 0) {
    if (!fallbackFrame) return null;

    return {
      id: sectionId,
      sectionId,
      x: fallbackFrame.frameX,
      y: fallbackFrame.frameY,
      w: fallbackFrame.frameW,
      h: fallbackFrame.frameH,
    };
  }

  const minX = Math.min(...subAreas.map((item) => item.x));
  const minY = Math.min(...subAreas.map((item) => item.y));
  const maxX = Math.max(...subAreas.map((item) => item.x + item.w));
  const maxY = Math.max(...subAreas.map((item) => item.y + item.h));
  const frameX = minX - FRAME_CONTENT_OFFSET_X - AREA_INSET;
  const frameY = minY - FRAME_CONTENT_OFFSET_Y - AREA_INSET;
  const frameW = maxX - frameX + AREA_INSET + FRAME_RIGHT_PADDING;
  const frameH = maxY - frameY + AREA_INSET + FRAME_BOTTOM_PADDING;

  return {
    id: sectionId,
    sectionId,
    x: frameX,
    y: frameY,
    w: frameW,
    h: frameH,
  };
}

function layoutSectionSubAreas(subAreas: WorldSubAreaLayout[]) {
  if (subAreas.length === 0) return [];

  const gap = 20;
  const totalWidth = subAreas.reduce((sum, item) => sum + item.w, 0);
  const targetRowWidth = Math.max(340, Math.min(620, Math.sqrt(totalWidth * 320)));
  let cursorX = 0;
  let cursorY = 0;
  let rowHeight = 0;

  return subAreas.map((item) => {
    if (cursorX > 0 && cursorX + item.w > targetRowWidth) {
      cursorX = 0;
      cursorY += rowHeight + gap;
      rowHeight = 0;
    }

    const positioned = {
      ...item,
      x: cursorX,
      y: cursorY,
    };

    cursorX += item.w + gap;
    rowHeight = Math.max(rowHeight, item.h);

    return positioned;
  });
}

export function InfiniteBoard({
  project,
  areas,
  onPersistAreaDelta,
  onPersistAreaFrame,
  onPersistSubdomainLayout,
  onCreateArea,
  onCreateSubdomain,
  onUpdateAreaMetadata,
  onUpdateSubdomainMetadata,
  onDeleteArea,
  onDeleteSubdomain,
  agents,
  agentChatStatus,
  focusedSectionId,
  focusedItemId,
  focusRequestKey,
  onRunAnalysis,
  analysisUpToDate,
}: {
  project: Project | null;
  areas: WorkspaceArea[];
  onPersistAreaDelta: (areaId: string, updates: Array<{ id: string; x: number; y: number }>) => Promise<void>;
  onPersistAreaFrame: (
    areaId: string,
    frame: { frameX: number; frameY: number; frameW: number; frameH: number },
  ) => Promise<void>;
  onPersistSubdomainLayout: (
    areaId: string,
    subdomainId: string,
    layout: { x: number; y: number; w: number; h: number },
  ) => Promise<void>;
  onCreateArea: (input: { name: string; description: string }) => Promise<string | null>;
  onCreateSubdomain: (areaId: string, input: { name: string; description: string }) => Promise<string | null | void>;
  onUpdateAreaMetadata: (
    areaId: string,
    input: { name: string; description: string },
  ) => Promise<void>;
  onUpdateSubdomainMetadata: (
    areaId: string,
    subdomainId: string,
    input: { name: string; description: string },
  ) => Promise<void>;
  onDeleteArea: (areaId: string) => Promise<void>;
  onDeleteSubdomain: (areaId: string, subdomainId: string) => Promise<void>;
  agents: OrgChartItem[];
  agentChatStatus?: Record<string, { isTyping: boolean; unreadCount: number }>;
  focusedSectionId: string | null;
  focusedItemId: string | null;
  focusRequestKey: number;
  onRunAnalysis: () => void;
  analysisUpToDate: boolean;
}) {
  const boardRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<Viewport>({ x: 0, y: 0, zoom: 1 });
  const sectionFramesRef = useRef<SectionFrame[]>([]);
  const subAreasRef = useRef<WorldSubAreaLayout[]>(flattenAreasToWorld(areas));
  const subAreaNodesRef = useRef<Record<string, HTMLDivElement | null>>({});
  const [frozenFrames, setFrozenFrames] = useState<Record<string, SectionFrame>>({});
  const [frameOverrides, setFrameOverrides] = useState<Record<string, SectionFrame>>({});
  const [selectedSectionIdState, setSelectedSectionIdState] = useState<string>(areas[0]?.id ?? "");
  const [editingAreaId, setEditingAreaId] = useState<string | null>(null);
  const [editingSubAreaId, setEditingSubAreaId] = useState<string | null>(null);
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, zoom: 1 });
  const [boardSize, setBoardSize] = useState({ width: 0, height: 0 });
  const [subAreaOverrides, setSubAreaOverrides] = useState<Record<string, Pick<WorldSubAreaLayout, "x" | "y" | "w" | "h">>>({});
  const dragState = useRef<{
    pointerId: number;
    start: Point;
    origin: Point;
  } | null>(null);

  const firstAreaId = areas[0]?.id ?? "";

  useEffect(() => {
    const element = boardRef.current;
    if (!element) return;

    const updateSize = () => {
      setBoardSize({
        width: element.clientWidth,
        height: element.clientHeight,
      });
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const cameraLabel = useMemo(
    () => `x ${Math.round(viewport.x)} | y ${Math.round(viewport.y)} | zoom ${Math.round(viewport.zoom * 100)}%`,
    [viewport],
  );
  const activeProjectLabel = project?.name ?? "No project selected";
  const subAreas = useMemo(
    () =>
      flattenAreasToWorld(areas).map((item) => ({
        ...item,
        ...(subAreaOverrides[item.id] ?? {}),
      })),
    [areas, subAreaOverrides],
  );
  const areasById = useMemo(
    () => new Map(areas.map((area) => [area.id, area])),
    [areas],
  );
  const sectionFrames = useMemo(() => {
    return areas
      .map((area) =>
        deriveSectionFrame(area.id, subAreas.filter((item) => item.sectionId === area.id), {
          frameX: area.frameX,
          frameY: area.frameY,
          frameW: area.frameW,
          frameH: area.frameH,
        }),
      )
      .filter((frame): frame is SectionFrame => frame !== null);
  }, [areas, subAreas]);
  const sectionSubAreas = useMemo(() => {
    const grouped = new Map<string, WorldSubAreaLayout[]>();
    for (const item of subAreas) {
      const current = grouped.get(item.sectionId);
      if (current) {
        current.push(item);
      } else {
        grouped.set(item.sectionId, [item]);
      }
    }
    return grouped;
  }, [subAreas]);
  const selectedSectionId = areas.some((area) => area.id === selectedSectionIdState)
    ? selectedSectionIdState
    : firstAreaId;
  const activeSectionId = focusedSectionId ?? selectedSectionId;
  const orderedFrames = useMemo(() => {
    const activeFrame = sectionFrames.find((frame) => frame.sectionId === activeSectionId);
    if (!activeFrame) return sectionFrames;
    return [...sectionFrames.filter((frame) => frame.sectionId !== activeSectionId), activeFrame];
  }, [activeSectionId, sectionFrames]);
  const agentCursors = useMemo<CursorPlacement[]>(
    () =>
      agents.map((agent) => ({
        id: agent.id,
        x: -720 + seededUnit(`${agent.id}:x`) * 1440,
        y: -480 + seededUnit(`${agent.id}:y`) * 960,
        name: agent.name,
        job: agent.job,
        driftX: -8 + seededUnit(`${agent.id}:dx`) * 16,
        driftY: -6 + seededUnit(`${agent.id}:dy`) * 12,
        duration: 9 + seededUnit(`${agent.id}:duration`) * 7,
        delay: -seededUnit(`${agent.id}:delay`) * 6,
        isTyping: agentChatStatus?.[agent.id]?.isTyping ?? false,
        unreadCount: agentChatStatus?.[agent.id]?.unreadCount ?? 0,
      })),
    [agentChatStatus, agents],
  );

  useEffect(() => {
    viewportRef.current = viewport;
  }, [viewport]);

  useEffect(() => {
    sectionFramesRef.current = sectionFrames;
  }, [sectionFrames]);

  useEffect(() => {
    subAreasRef.current = subAreas;
  }, [subAreas]);

  useEffect(() => {
    const padding = 96;
    if (boardSize.width === 0 || boardSize.height === 0) return;

    let centerX = 0;
    let centerY = 0;
    let fittedZoom = 1;

    if (focusedSectionId && focusedItemId) {
      const frame = sectionFramesRef.current.find((entry) => entry.sectionId === focusedSectionId);
      const node = subAreaNodesRef.current[`${focusedSectionId}:${focusedItemId}`];
      const boardRect = boardRef.current?.getBoundingClientRect();

      if (frame && node && boardRect) {
        const rect = node.getBoundingClientRect();
        const currentViewport = viewportRef.current;
        const worldX = (rect.left - boardRect.left - boardSize.width / 2 - currentViewport.x) / currentViewport.zoom;
        const worldY = (rect.top - boardRect.top - boardSize.height / 2 - currentViewport.y) / currentViewport.zoom;
        const worldWidth = rect.width / currentViewport.zoom;
        const worldHeight = rect.height / currentViewport.zoom;

        fittedZoom = clampZoom(
          Math.min(
            (boardSize.width - padding * 2) / worldWidth,
            (boardSize.height - padding * 2) / worldHeight,
          ),
        );
        centerX = worldX + worldWidth / 2;
        centerY = worldY + worldHeight / 2;
      } else if (frame) {
        fittedZoom = clampZoom(
          Math.min(
            (boardSize.width - padding * 2) / frame.w,
            (boardSize.height - padding * 2) / frame.h,
          ),
        );
        centerX = frame.x + frame.w / 2;
        centerY = frame.y + frame.h / 2;
      } else {
        return;
      }
    } else if (focusedSectionId) {
      const frame = sectionFramesRef.current.find((entry) => entry.sectionId === focusedSectionId);
      if (!frame) return;

      fittedZoom = clampZoom(
        Math.min(
          (boardSize.width - padding * 2) / frame.w,
          (boardSize.height - padding * 2) / frame.h,
        ),
      );
      centerX = frame.x + frame.w / 2;
      centerY = frame.y + frame.h / 2;
    } else {
      return;
    }

    const animationFrame = requestAnimationFrame(() => {
      setViewport({
        x: -centerX * fittedZoom,
        y: -centerY * fittedZoom,
        zoom: fittedZoom,
      });
    });

    return () => cancelAnimationFrame(animationFrame);
  }, [boardSize.height, boardSize.width, focusRequestKey, focusedItemId, focusedSectionId]);

  function moveSection(sectionId: string, deltaX: number, deltaY: number) {
    setSubAreaOverrides((current) => {
      const next = { ...current };
      for (const item of sectionSubAreas.get(sectionId) ?? []) {
        next[item.id] = {
          x: (current[item.id]?.x ?? item.x) + deltaX,
          y: (current[item.id]?.y ?? item.y) + deltaY,
          w: current[item.id]?.w ?? item.w,
          h: current[item.id]?.h ?? item.h,
        };
      }
      return next;
    });
  }

  function moveSubArea(sectionId: string, itemId: string, deltaX: number, deltaY: number) {
    const item = (sectionSubAreas.get(sectionId) ?? []).find((entry) => entry.id === itemId);
    if (!item) return;

    setSubAreaOverrides((current) => ({
      ...current,
      [itemId]: {
        x: (current[itemId]?.x ?? item.x) + deltaX,
        y: (current[itemId]?.y ?? item.y) + deltaY,
        w: current[itemId]?.w ?? item.w,
        h: current[itemId]?.h ?? item.h,
      },
    }));
  }

  function resizeSubArea(
    sectionId: string,
    frame: SectionFrame,
    itemId: string,
    nextLayout: Pick<WorkspaceSubAreaLayout, "x" | "y" | "w" | "h">,
  ) {
    setSubAreaOverrides((current) => ({
      ...current,
      [itemId]: {
        x: frame.x + FRAME_CONTENT_OFFSET_X + nextLayout.x,
        y: frame.y + FRAME_CONTENT_OFFSET_Y + nextLayout.y,
        w: nextLayout.w,
        h: nextLayout.h,
      },
    }));
  }

  function freezeSectionFrame(sectionId: string) {
    const currentFrame = sectionFramesRef.current.find((frame) => frame.sectionId === sectionId);
    if (!currentFrame) return;

    setFrozenFrames((current) => (current[sectionId] ? current : { ...current, [sectionId]: currentFrame }));
  }

  function releaseSectionFrame(sectionId: string) {
    setFrozenFrames((current) => {
      if (!current[sectionId]) return current;
      const next = { ...current };
      delete next[sectionId];
      return next;
    });
  }

  async function persistSection(sectionId: string) {
    const current = subAreasRef.current.filter((item) => item.sectionId === sectionId);
    if (current.length > 0) {
      await onPersistAreaDelta(
        sectionId,
        current.map((item) => ({ id: item.id, x: item.x, y: item.y })),
      );
      return;
    }

    const frame = sectionFramesRef.current.find((item) => item.sectionId === sectionId);
    if (!frame) return;
    await onPersistAreaFrame(sectionId, {
      frameX: frame.x,
      frameY: frame.y,
      frameW: frame.w,
      frameH: frame.h,
    });
  }

  async function persistSubArea(sectionId: string, itemId: string) {
    const current = subAreasRef.current.find((item) => item.sectionId === sectionId && item.id === itemId);
    if (!current) return;
    await onPersistSubdomainLayout(sectionId, itemId, {
      x: current.x,
      y: current.y,
      w: current.w,
      h: current.h,
    });
  }

  function handlePointerDown(event: React.PointerEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget) return;
    setSelectedSectionIdState("");

    dragState.current = {
      pointerId: event.pointerId,
      start: { x: event.clientX, y: event.clientY },
      origin: { x: viewport.x, y: viewport.y },
    };

    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handlePointerMove(event: React.PointerEvent<HTMLDivElement>) {
    const drag = dragState.current;
    if (!drag || drag.pointerId !== event.pointerId) return;

    setViewport((current) => ({
      ...current,
      x: drag.origin.x + event.clientX - drag.start.x,
      y: drag.origin.y + event.clientY - drag.start.y,
    }));
  }

  function endPointer(event: React.PointerEvent<HTMLDivElement>) {
    const drag = dragState.current;
    if (!drag || drag.pointerId !== event.pointerId) return;

    dragState.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  function handleWheel(event: React.WheelEvent<HTMLDivElement>) {
    event.preventDefault();

    const rect = event.currentTarget.getBoundingClientRect();
    const pointer = {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };

    setViewport((current) => {
      const previousZoom = current.zoom;
      const nextZoom = clampZoom(previousZoom * Math.exp(-event.deltaY * 0.0012));
      if (nextZoom === previousZoom) return current;

      const local = {
        x: pointer.x - boardSize.width / 2 - current.x,
        y: pointer.y - boardSize.height / 2 - current.y,
      };
      const scaleRatio = nextZoom / previousZoom;

      return {
        zoom: nextZoom,
        x: current.x - local.x * (scaleRatio - 1),
        y: current.y - local.y * (scaleRatio - 1),
      };
    });
  }

  async function handleRelaxLayout() {
    const relaxedAreas: Array<{ areaId: string; updates: Array<{ id: string; x: number; y: number }> }> = [];
    const relaxedFrames: Array<{ areaId: string; frameX: number; frameY: number; frameW: number; frameH: number }> = [];
    const nextSubAreas: WorldSubAreaLayout[] = [];
    const sectionGap = 72;
    const rowGap = 88;
    const maxCanvasRowWidth = 1680;
    let cursorX = 0;
    let cursorY = 0;
    let rowHeight = 0;

    for (const area of areas) {
      const orderedSubAreas = (sectionSubAreas.get(area.id) ?? [])
        .slice()
        .sort((left, right) => {
          const leftOrder = area.subdomains.findIndex((item) => item.id === left.id);
          const rightOrder = area.subdomains.findIndex((item) => item.id === right.id);
          return leftOrder - rightOrder;
        });
      const localSubAreas = layoutSectionSubAreas(orderedSubAreas);
      const localBounds = deriveSectionFrame(area.id, localSubAreas, {
        frameX: area.frameX,
        frameY: area.frameY,
        frameW: area.frameW,
        frameH: area.frameH,
      }) ?? {
        id: area.id,
        sectionId: area.id,
        x: -FRAME_CONTENT_OFFSET_X - AREA_INSET,
        y: -FRAME_CONTENT_OFFSET_Y - AREA_INSET,
        w: area.frameW,
        h: area.frameH,
      };

      if (cursorX > 0 && cursorX + localBounds.w > maxCanvasRowWidth) {
        cursorX = 0;
        cursorY += rowHeight + rowGap;
        rowHeight = 0;
      }

      const areaOriginX = cursorX - localBounds.x;
      const areaOriginY = cursorY - localBounds.y;
      const updates = localSubAreas.map((item) => ({
        id: item.id,
        x: areaOriginX + item.x,
        y: areaOriginY + item.y,
      }));

      relaxedAreas.push({ areaId: area.id, updates });
      relaxedFrames.push({
        areaId: area.id,
        frameX: areaOriginX + localBounds.x,
        frameY: areaOriginY + localBounds.y,
        frameW: localBounds.w,
        frameH: localBounds.h,
      });
      nextSubAreas.push(
        ...orderedSubAreas.map((item) => {
          const update = updates.find((entry) => entry.id === item.id);
          return {
            ...item,
            x: update?.x ?? item.x,
            y: update?.y ?? item.y,
          };
        }),
      );

      cursorX += localBounds.w + sectionGap;
      rowHeight = Math.max(rowHeight, localBounds.h);
    }

    setSubAreaOverrides(
      Object.fromEntries(
        nextSubAreas.map((item) => [
          item.id,
          {
            x: item.x,
            y: item.y,
            w: item.w,
            h: item.h,
          },
        ]),
      ),
    );
    subAreasRef.current = nextSubAreas;
    await Promise.all([
      ...relaxedAreas.map((area) => (
        area.updates.length > 0
          ? onPersistAreaDelta(area.areaId, area.updates)
          : Promise.resolve()
      )),
      ...relaxedFrames.map((frame) => onPersistAreaFrame(frame.areaId, frame)),
    ]);
  }

  async function handleCreateArea() {
    const areaId = await onCreateArea({
      name: "Untitled Domain",
      description: "",
    });
    if (!areaId) return;

    setEditingAreaId(areaId);
    setSelectedSectionIdState(areaId);
  }

  return (
    <div className="workspace-board" ref={boardRef}>
      <div
        className="workspace-board__pane"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={endPointer}
        onPointerCancel={endPointer}
        onWheel={handleWheel}
      >
        <div className="workspace-board__hud workspace-board__hud--left">
          <span>{activeProjectLabel}</span>
          <span>{project?.description || "Select a project, then start arranging mixed-media references."}</span>
        </div>

        <div className="workspace-board__hud workspace-board__hud--right">
          <span>{cameraLabel}</span>
          <span>Drag to pan, scroll to zoom</span>
        </div>

        <div className="workspace-board__floating-actions">
          <button
            type="button"
            className="workspace-board__floating-action"
            onPointerDown={(event) => event.stopPropagation()}
            onClick={(event) => {
              event.stopPropagation();
              void handleCreateArea();
            }}
            aria-label="Add domain"
          >
            <Plus size={16} />
          </button>
          <button
            type="button"
            className="workspace-board__floating-action"
            onPointerDown={(event) => event.stopPropagation()}
            onClick={(event) => {
              event.stopPropagation();
              void handleRelaxLayout();
            }}
            aria-label="Relax workspace cards"
          >
            <Sparkles size={16} />
          </button>
          <button
            type="button"
            className={`workspace-board__floating-action${!analysisUpToDate ? " workspace-board__floating-action--stale" : ""}`}
            onPointerDown={(event) => event.stopPropagation()}
            onClick={(event) => {
              event.stopPropagation();
              onRunAnalysis();
            }}
            aria-label="Re-run site analysis"
          >
            <RefreshCw size={16} />
          </button>
        </div>

        <div
          className="workspace-board__world"
          style={{
            transform: `translate(${boardSize.width / 2 + viewport.x}px, ${boardSize.height / 2 + viewport.y}px) scale(${viewport.zoom})`,
          }}
        >
          <div className="workspace-board__grid workspace-board__grid--major" />
          <div className="workspace-board__grid workspace-board__grid--minor" />

          {agentCursors.map((cursor) => (
            <div
              key={cursor.id}
              className="workspace-agent-cursor"
              style={{
                left: cursor.x,
                top: cursor.y,
                ["--workspace-cursor-drift-x" as string]: `${cursor.driftX}px`,
                ["--workspace-cursor-drift-y" as string]: `${cursor.driftY}px`,
                ["--workspace-cursor-duration" as string]: `${cursor.duration}s`,
                ["--workspace-cursor-delay" as string]: `${cursor.delay}s`,
              }}
            >
              <Image
                className="workspace-agent-cursor__image"
                src="/icons/cursor.png"
                alt=""
                width={18}
                height={18}
                aria-hidden="true"
              />
              <div className="workspace-agent-cursor__label">
                <span className="workspace-agent-cursor__name-row">
                  <span className="workspace-agent-cursor__name">{cursor.name}</span>
                  {cursor.isTyping ? (
                    <span className="workspace-agent-cursor__typing" aria-label={`${cursor.name} is typing`}>
                      <span className="workspace-agent-cursor__typing-dot" />
                      <span className="workspace-agent-cursor__typing-dot" />
                      <span className="workspace-agent-cursor__typing-dot" />
                    </span>
                  ) : null}
                  {cursor.unreadCount > 0 ? (
                    <span className="workspace-agent-cursor__unread-badge">{cursor.unreadCount}</span>
                  ) : null}
                </span>
                <span className="workspace-agent-cursor__job">{cursor.job}</span>
              </div>
            </div>
          ))}

          {orderedFrames.map((frame) => {
            const section = areasById.get(frame.sectionId);
            if (!section) return null;

            const renderFrame = frozenFrames[frame.sectionId] ?? frameOverrides[frame.sectionId] ?? frame;
            const localSubAreas = (sectionSubAreas.get(frame.sectionId) ?? []).map((item) => ({
              id: item.id,
              x: item.x - renderFrame.x - FRAME_CONTENT_OFFSET_X,
              y: item.y - renderFrame.y - FRAME_CONTENT_OFFSET_Y,
              w: item.w,
              h: item.h,
            }));

            return (
              <Rnd
                key={frame.id}
                className="workspace-card-shell"
                position={{ x: renderFrame.x, y: renderFrame.y }}
                size={{ width: renderFrame.w, height: renderFrame.h }}
                scale={viewport.zoom}
                enableResizing={false}
                cancel=".workspace-worksubarea-shell, .workspace-worksubarea__resize-handle, .workspace-card-action"
                style={{ zIndex: activeSectionId === frame.sectionId ? 5 : 2 }}
                onDragStart={() => {
                  setSelectedSectionIdState(frame.sectionId);
                  dragState.current = null;
                }}
                onDrag={(_, data) => {
                  setSelectedSectionIdState(frame.sectionId);
                  if ((sectionSubAreas.get(frame.sectionId) ?? []).length === 0) {
                    setFrameOverrides((current) => ({
                      ...current,
                      [frame.sectionId]: {
                        ...(current[frame.sectionId] ?? renderFrame),
                        x: (current[frame.sectionId]?.x ?? renderFrame.x) + data.deltaX,
                        y: (current[frame.sectionId]?.y ?? renderFrame.y) + data.deltaY,
                      },
                    }));
                  } else {
                    moveSection(frame.sectionId, data.deltaX, data.deltaY);
                  }
                }}
                onDragStop={() => {
                  if ((sectionSubAreas.get(frame.sectionId) ?? []).length === 0) {
                    const nextFrame = frameOverrides[frame.sectionId] ?? renderFrame;
                    void onPersistAreaFrame(frame.sectionId, {
                      frameX: nextFrame.x,
                      frameY: nextFrame.y,
                      frameW: nextFrame.w,
                      frameH: nextFrame.h,
                    });
                  } else {
                    void persistSection(frame.sectionId);
                  }
                }}
              >
                <PlaceholderCard
                  sectionId={frame.sectionId}
                  section={section}
                  subAreas={localSubAreas}
                  selected={activeSectionId === frame.sectionId}
                  viewportZoom={viewport.zoom}
                  autoEditArea={editingAreaId === frame.sectionId}
                  autoEditSubAreaId={editingSubAreaId && section.subdomains.some((item) => item.id === editingSubAreaId) ? editingSubAreaId : null}
                  onSelect={() => setSelectedSectionIdState(frame.sectionId)}
                  onMoveSubArea={(itemId, deltaX, deltaY) => moveSubArea(frame.sectionId, itemId, deltaX, deltaY)}
                  onResizeSubArea={(itemId, nextLayout) => resizeSubArea(frame.sectionId, renderFrame, itemId, nextLayout)}
                  onSubAreaGestureStart={freezeSectionFrame}
                  onSubAreaGestureEnd={(sectionId, itemId) => {
                    releaseSectionFrame(sectionId);
                    void persistSubArea(sectionId, itemId);
                  }}
                  onCreateSubdomain={async (areaId, input) => {
                    const createdId = await onCreateSubdomain(areaId, input);
                    setFrameOverrides((current) => {
                      if (!current[areaId]) return current;
                      const next = { ...current };
                      delete next[areaId];
                      return next;
                    });
                    if (createdId) {
                      setEditingSubAreaId(createdId);
                    }
                    return createdId;
                  }}
                  onUpdateAreaMetadata={async (areaId, input) => {
                    await onUpdateAreaMetadata(areaId, input);
                    setEditingAreaId(null);
                  }}
                  onUpdateSubdomainMetadata={async (areaId, subdomainId, input) => {
                    await onUpdateSubdomainMetadata(areaId, subdomainId, input);
                    setEditingSubAreaId(null);
                  }}
                  onDeleteArea={async (areaId) => {
                    await onDeleteArea(areaId);
                    setEditingAreaId((current) => (current === areaId ? null : current));
                  }}
                  onDeleteSubdomain={async (areaId, subdomainId) => {
                    await onDeleteSubdomain(areaId, subdomainId);
                    setEditingSubAreaId((current) => (current === subdomainId ? null : current));
                  }}
                  onSubAreaNodeChange={(sectionId, itemId, node) => {
                    subAreaNodesRef.current[`${sectionId}:${itemId}`] = node;
                  }}
                />
              </Rnd>
            );
          })}

          <div className="workspace-board__origin">
            <span>Origin</span>
          </div>
        </div>
      </div>
    </div>
  );
}
