import { useEffect, useState, type PropsWithChildren, type ReactNode } from "react";
import { Pencil, Trash2, X, Check } from "lucide-react";

type WorkAreaProps = PropsWithChildren<{
  title: string;
  description: string;
  mode: string;
  isEditing?: boolean;
  autoFocus?: boolean;
  editDisabled?: boolean;
  deleteDisabled?: boolean;
  footerAction?: ReactNode;
  onStartEdit?: () => void;
  onDelete?: () => void;
  onSubmitEdit?: (value: { name: string; description: string }) => Promise<void> | void;
  onCancelEdit?: () => void;
}>;

export function WorkArea({
  title,
  description,
  mode,
  isEditing = false,
  autoFocus = false,
  editDisabled = false,
  deleteDisabled = false,
  children,
  footerAction,
  onStartEdit,
  onDelete,
  onSubmitEdit,
  onCancelEdit,
}: WorkAreaProps) {
  const [draftName, setDraftName] = useState(title);
  const [draftDescription, setDraftDescription] = useState(description);

  useEffect(() => {
    if (!isEditing) return;
    if (!autoFocus) return;

    const frame = requestAnimationFrame(() => {
      const input = document.querySelector<HTMLInputElement>(".workspace-workarea__title-input");
      input?.focus();
      input?.select();
    });

    return () => cancelAnimationFrame(frame);
  }, [autoFocus, isEditing]);

  return (
    <section className="workspace-workarea">
      <div className="workspace-workarea__header">
        <div className="workspace-workarea__heading">
          {isEditing ? (
            <>
              <input
                className="workspace-workarea__title-input workspace-workarea__field"
                value={draftName}
                onChange={(event) => setDraftName(event.target.value)}
                placeholder="Domain name"
              />
              <textarea
                className="workspace-workarea__description-input workspace-workarea__field"
                value={draftDescription}
                onChange={(event) => setDraftDescription(event.target.value)}
                placeholder="Domain description"
                rows={3}
              />
            </>
          ) : (
            <>
              <h3 className="workspace-workarea__title">{title}</h3>
              {description ? <p className="workspace-workarea__description">{description}</p> : null}
            </>
          )}
          <div className="workspace-workarea__meta">{mode}</div>
        </div>
        <div className="workspace-workarea__actions">
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
                aria-label="Save domain"
              >
                <Check size={14} />
              </button>
              <button
                type="button"
                className="workspace-card-action"
                onPointerDown={(event) => event.stopPropagation()}
                onClick={(event) => {
                  event.stopPropagation();
                  setDraftName(title);
                  setDraftDescription(description);
                  onCancelEdit?.();
                }}
                aria-label="Cancel domain editing"
              >
                <X size={14} />
              </button>
            </>
          ) : (
            <>
              {onStartEdit || editDisabled ? (
                <button
                  type="button"
                  className="workspace-card-action"
                  disabled={editDisabled}
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={(event) => {
                    event.stopPropagation();
                    if (editDisabled) return;
                    onStartEdit?.();
                  }}
                  aria-label={`Edit ${title}`}
                >
                  <Pencil size={14} />
                </button>
              ) : null}
              {onDelete || deleteDisabled ? (
                <button
                  type="button"
                  className="workspace-card-action workspace-card-action--danger"
                  disabled={deleteDisabled}
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={(event) => {
                    event.stopPropagation();
                    if (deleteDisabled) return;
                    onDelete?.();
                  }}
                  aria-label={`Delete ${title}`}
                >
                  <Trash2 size={14} />
                </button>
              ) : null}
            </>
          )}
        </div>
      </div>
      <div className="workspace-workarea__canvas">
        {children}
      </div>
      {footerAction ? (
        <div className="workspace-workarea__footer-action">
          {footerAction}
        </div>
      ) : null}
    </section>
  );
}
