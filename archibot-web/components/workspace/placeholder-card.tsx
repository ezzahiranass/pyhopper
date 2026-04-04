import { useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { Rnd } from "react-rnd";
import type { WorkspaceArea } from "@/components/studio/types";
import { WorkArea } from "@/components/workspace/work-area";
import { WorkSubArea } from "@/components/workspace/work-sub-area";
import { SUBAREA_MIN_HEIGHT, SUBAREA_MIN_WIDTH } from "@/components/workspace/workspace-data";

export type WorkspaceSubAreaLayout = {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
};

type PlaceholderCardProps = {
  sectionId: string;
  section: WorkspaceArea;
  subAreas: WorkspaceSubAreaLayout[];
  selected: boolean;
  viewportZoom: number;
  autoEditArea?: boolean;
  autoEditSubAreaId?: string | null;
  onSelect: () => void;
  onMoveSubArea: (itemId: string, deltaX: number, deltaY: number) => void;
  onResizeSubArea: (
    itemId: string,
    nextLayout: Pick<WorkspaceSubAreaLayout, "x" | "y" | "w" | "h">,
  ) => void;
  onSubAreaGestureStart: (sectionId: string) => void;
  onSubAreaGestureEnd: (sectionId: string, itemId: string) => void;
  onSubAreaNodeChange: (sectionId: string, itemId: string, node: HTMLDivElement | null) => void;
  onCreateSubdomain: (sectionId: string, input: { name: string; description: string }) => Promise<string | null | void>;
  onUpdateAreaMetadata: (
    sectionId: string,
    input: { name: string; description: string },
  ) => Promise<void>;
  onUpdateSubdomainMetadata: (
    sectionId: string,
    subdomainId: string,
    input: { name: string; description: string },
  ) => Promise<void>;
  onDeleteArea: (sectionId: string) => Promise<void>;
  onDeleteSubdomain: (sectionId: string, subdomainId: string) => Promise<void>;
};

export function PlaceholderCard({
  sectionId,
  section,
  subAreas,
  selected,
  viewportZoom,
  autoEditArea = false,
  autoEditSubAreaId = null,
  onSelect,
  onMoveSubArea,
  onResizeSubArea,
  onSubAreaGestureStart,
  onSubAreaGestureEnd,
  onSubAreaNodeChange,
  onCreateSubdomain,
  onUpdateAreaMetadata,
  onUpdateSubdomainMetadata,
  onDeleteArea,
  onDeleteSubdomain,
}: PlaceholderCardProps) {
  const [selectedSubAreaId, setSelectedSubAreaId] = useState<string>(section.subdomains[0]?.id ?? "");
  const [editingAreaState, setEditingAreaState] = useState<boolean | null>(null);
  const [editingSubAreaId, setEditingSubAreaId] = useState<string | null>(null);
  const [dismissedAutoEditSubAreaId, setDismissedAutoEditSubAreaId] = useState<string | null>(null);
  const itemsById = useMemo(
    () => new Map(section.subdomains.map((item) => [item.id, item])),
    [section.subdomains],
  );
  const activeSubAreaId = itemsById.has(selectedSubAreaId) ? selectedSubAreaId : section.subdomains[0]?.id ?? "";
  const editingArea = editingAreaState ?? autoEditArea;
  const derivedAutoEditSubAreaId =
    autoEditSubAreaId && autoEditSubAreaId !== dismissedAutoEditSubAreaId && itemsById.has(autoEditSubAreaId)
      ? autoEditSubAreaId
      : null;
  const activeEditingSubAreaId = editingSubAreaId ?? derivedAutoEditSubAreaId;

  async function handleCreateSubdomain() {
    const createdId = await onCreateSubdomain(sectionId, {
      name: "Untitled Domain",
      description: "",
    });

    if (createdId) {
      setDismissedAutoEditSubAreaId(null);
      setEditingSubAreaId(createdId);
      setSelectedSubAreaId(createdId);
    }
  }

  return (
    <div
      className={`workspace-card workspace-card--placeholder${selected ? " is-selected" : ""}`}
      onPointerDown={onSelect}
    >
      <WorkArea
        title={section.name}
        description={section.description}
        mode={section.type}
        isEditing={editingArea}
        autoFocus={editingArea}
        editDisabled={section.isLocked}
        deleteDisabled={section.isLocked}
        onStartEdit={() => setEditingAreaState(true)}
        onCancelEdit={() => setEditingAreaState(false)}
        onSubmitEdit={async (value) => {
          if (!value.name.trim()) return;
          await onUpdateAreaMetadata(sectionId, value);
          setEditingAreaState(false);
        }}
        onDelete={() => {
          void onDeleteArea(sectionId);
        }}
        key={`${section.id}:${section.name}:${section.description}:${editingArea ? "editing" : "view"}`}
        footerAction={(
          <button
            type="button"
            className="workspace-workarea__add-button workspace-card-action"
            onPointerDown={(event) => event.stopPropagation()}
            onClick={(event) => {
              event.stopPropagation();
              void handleCreateSubdomain();
            }}
            aria-label={`Add domain to ${section.name}`}
          >
            <Plus size={15} />
          </button>
        )}
      >
        {subAreas.map((layout) => {
          const item = itemsById.get(layout.id);
          if (!item) return null;

          return (
            <Rnd
              key={layout.id}
              className={`workspace-worksubarea-shell${activeSubAreaId === layout.id ? " is-selected" : ""}`}
              position={{ x: layout.x, y: layout.y }}
              size={{ width: layout.w, height: layout.h }}
              style={{ zIndex: activeSubAreaId === layout.id ? 3 : 1 }}
              scale={viewportZoom}
              minWidth={SUBAREA_MIN_WIDTH}
              minHeight={SUBAREA_MIN_HEIGHT}
              cancel=".workspace-card-action, .workspace-worksubarea__field, .workspace-artifact__interactive, .maplibregl-canvas, .maplibregl-control-container"
              enableResizing={{
                topLeft: true,
                bottomRight: true,
              }}
              resizeHandleComponent={{
                topLeft: <span className="workspace-worksubarea__resize-handle workspace-worksubarea__resize-handle--top-left" />,
                bottomRight: <span className="workspace-worksubarea__resize-handle" />,
              }}
              onDragStart={() => {
                onSelect();
                setSelectedSubAreaId(layout.id);
                onSubAreaGestureStart(sectionId);
              }}
              onDrag={(_, data) => {
                onSelect();
                setSelectedSubAreaId(layout.id);
                onMoveSubArea(layout.id, data.deltaX, data.deltaY);
              }}
              onDragStop={() => {
                onSubAreaGestureEnd(sectionId, layout.id);
              }}
              onResizeStart={() => {
                onSelect();
                setSelectedSubAreaId(layout.id);
                onSubAreaGestureStart(sectionId);
              }}
              onResize={(_, __, ref, ___, position) => {
                onSelect();
                setSelectedSubAreaId(layout.id);
                onResizeSubArea(layout.id, {
                  x: position.x,
                  y: position.y,
                  w: ref.offsetWidth,
                  h: ref.offsetHeight,
                });
              }}
              onResizeStop={() => {
                onSubAreaGestureEnd(sectionId, layout.id);
              }}
            >
              <WorkSubArea
                ref={(node) => onSubAreaNodeChange(sectionId, layout.id, node)}
                subdomainId={item.id}
                label={item.name}
                description={item.description}
                content={item.content}
                artifacts={item.artifacts}
                selected={activeSubAreaId === layout.id}
                isEditing={activeEditingSubAreaId === layout.id}
                autoFocus={activeEditingSubAreaId === layout.id}
                editDisabled={item.isLocked}
                deleteDisabled={item.isLocked}
                key={`${layout.id}:${item.name}:${item.description}:${activeEditingSubAreaId === layout.id ? "editing" : "view"}`}
                onStartEdit={() => {
                  onSelect();
                  setSelectedSubAreaId(layout.id);
                  setDismissedAutoEditSubAreaId(null);
                  setEditingSubAreaId(layout.id);
                }}
                onCancelEdit={() => {
                  setDismissedAutoEditSubAreaId(autoEditSubAreaId ?? null);
                  setEditingSubAreaId(null);
                }}
                onSubmitEdit={async (value) => {
                  if (!value.name.trim()) return;
                  await onUpdateSubdomainMetadata(sectionId, layout.id, value);
                  setDismissedAutoEditSubAreaId(autoEditSubAreaId ?? null);
                  setEditingSubAreaId(null);
                }}
                onDelete={() => {
                  void onDeleteSubdomain(sectionId, layout.id);
                }}
                onClick={() => {
                  onSelect();
                  setSelectedSubAreaId(layout.id);
                }}
              />
            </Rnd>
          );
        })}
      </WorkArea>
    </div>
  );
}
