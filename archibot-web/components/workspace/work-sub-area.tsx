import { forwardRef, useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Check, Pencil, Trash2, X } from "lucide-react";
import type { WorkspaceArtifactMap } from "@/components/studio/types";
import { WorkspaceArtifactRenderer } from "@/components/workspace/artifacts/artifact-renderer";

type WorkSubAreaProps = {
  subdomainId: string;
  label: string;
  description?: string;
  content?: string | null;
  artifacts?: WorkspaceArtifactMap;
  selected: boolean;
  style?: CSSProperties;
  isEditing?: boolean;
  autoFocus?: boolean;
  editDisabled?: boolean;
  deleteDisabled?: boolean;
  onClick?: () => void;
  onStartEdit?: () => void;
  onDelete?: () => void;
  onSubmitEdit?: (value: { name: string; description: string }) => Promise<void> | void;
  onCancelEdit?: () => void;
};

export const WorkSubArea = forwardRef<HTMLDivElement, WorkSubAreaProps>(function WorkSubArea(
  {
    subdomainId,
    label,
    description,
    content,
    artifacts = {},
    selected,
    style,
    isEditing = false,
    autoFocus = false,
    editDisabled = false,
    deleteDisabled = false,
    onClick,
    onStartEdit,
    onDelete,
    onSubmitEdit,
    onCancelEdit,
  },
  ref,
) {
  const [draftName, setDraftName] = useState(label);
  const [draftDescription, setDraftDescription] = useState(description ?? "");
  const artifactEntries = Object.entries(artifacts);

  useEffect(() => {
    if (!isEditing || !autoFocus) return;

    const frame = requestAnimationFrame(() => {
      const input = document.querySelector<HTMLInputElement>(".workspace-worksubarea__name-input");
      input?.focus();
      input?.select();
    });

    return () => cancelAnimationFrame(frame);
  }, [autoFocus, isEditing]);

  return (
    <div
      ref={ref}
      className={`workspace-worksubarea${selected ? " is-selected" : ""}${isEditing ? " is-editing" : ""}`}
      style={style}
      onClick={onClick}
    >
      <div className="workspace-worksubarea__toolbar">
        {isEditing ? (
          <>
            <button
              type="button"
              className="workspace-card-action"
              onPointerDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation();
                void onSubmitEdit?.({
                  name: draftName.trim(),
                  description: draftDescription.trim(),
                });
              }}
              aria-label="Save subdomain"
            >
              <Check size={14} />
            </button>
            <button
              type="button"
              className="workspace-card-action"
              onPointerDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation();
                setDraftName(label);
                setDraftDescription(description ?? "");
                onCancelEdit?.();
              }}
              aria-label="Cancel subdomain editing"
            >
              <X size={14} />
            </button>
          </>
        ) : (
          <>
            {onStartEdit || editDisabled ? (
              <button
                type="button"
                className="workspace-card-action workspace-worksubarea__edit-button"
                disabled={editDisabled}
                onPointerDown={(event) => event.stopPropagation()}
                onClick={(event) => {
                  event.stopPropagation();
                  if (editDisabled) return;
                  onStartEdit?.();
                }}
                aria-label={`Edit ${label}`}
              >
                <Pencil size={14} />
              </button>
            ) : null}
            {onDelete || deleteDisabled ? (
              <button
                type="button"
                className="workspace-card-action workspace-card-action--danger workspace-worksubarea__delete-button"
                disabled={deleteDisabled}
                onPointerDown={(event) => event.stopPropagation()}
                onClick={(event) => {
                  event.stopPropagation();
                  if (deleteDisabled) return;
                  onDelete?.();
                }}
                aria-label={`Delete ${label}`}
              >
                <Trash2 size={14} />
              </button>
            ) : null}
          </>
        )}
      </div>
      <div className="workspace-worksubarea__content">
        {isEditing ? (
          <>
            <input
              className="workspace-worksubarea__name-input workspace-worksubarea__field"
              value={draftName}
              onChange={(event) => setDraftName(event.target.value)}
              placeholder="Domain name"
            />
            <textarea
              className="workspace-worksubarea__description-input workspace-worksubarea__field"
              value={draftDescription}
              onChange={(event) => setDraftDescription(event.target.value)}
              placeholder="Domain description"
              rows={3}
            />
          </>
        ) : (
          <>
            <span className="workspace-worksubarea__label">{label}</span>
            {description ? <span className="workspace-worksubarea__description">{description}</span> : null}
            {artifactEntries.length > 0 ? (
              <div className="workspace-worksubarea__artifact-list">
                {artifactEntries.map(([artifactId, artifact]) => (
                  <WorkspaceArtifactRenderer
                    key={artifactId}
                    artifactId={artifactId}
                    subdomainId={subdomainId}
                    artifact={artifact}
                  />
                ))}
              </div>
            ) : null}
            {content ? <p className="workspace-worksubarea__content-text">{content}</p> : null}
          </>
        )}
      </div>
    </div>
  );
});
