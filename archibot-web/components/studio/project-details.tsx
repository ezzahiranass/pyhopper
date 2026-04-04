"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, FileText, Pencil, Trash2, Upload, X } from "lucide-react";
import { SiteParcelMap } from "@/components/mapbox/site-parcel-map";
import { useStudio } from "@/components/studio/studio-context";
import { Project, ProjectAttachment } from "@/components/studio/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const PROJECT_TYPE_OPTIONS = [
  "Residential",
  "Commercial",
  "Mixed-use",
  "Office",
  "Hospitality",
  "Education",
  "Healthcare",
  "Industrial",
  "Cultural",
  "Other",
] as const;

type Props = {
  project: Project;
  onClose: () => void;
};

function formatAttachmentSize(size: number) {
  if (size >= 1_000_000) return `${(size / 1_000_000).toFixed(1)} MB`;
  if (size >= 1_000) return `${(size / 1_000).toFixed(1)} KB`;
  return `${size} B`;
}

export function ProjectDetails({ project, onClose }: Props) {
  const { updateProject } = useStudio();
  const initialProjectType = project.projectType || "Residential";
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description);
  const [projectType, setProjectType] = useState(initialProjectType);
  const [parcelDefinition, setParcelDefinition] = useState(project.parcelDefinition);
  const [attachmentsToAdd, setAttachmentsToAdd] = useState<File[]>([]);
  const [attachmentsToRemove, setAttachmentsToRemove] = useState<ProjectAttachment[]>([]);
  const [isDraggingAttachments, setIsDraggingAttachments] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const resetDraftState = useCallback(() => {
    setName(project.name);
    setDescription(project.description);
    setProjectType(project.projectType || "Residential");
    setParcelDefinition(project.parcelDefinition);
    setAttachmentsToAdd([]);
    setAttachmentsToRemove([]);
    setIsDraggingAttachments(false);
    setIsSaving(false);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, [project]);

  useEffect(() => {
    resetDraftState();
    setIsEditing(false);
  }, [project, resetDraftState]);

  const hasChanges =
    name.trim() !== project.name ||
    description.trim() !== project.description ||
    projectType !== initialProjectType ||
    JSON.stringify(parcelDefinition) !== JSON.stringify(project.parcelDefinition) ||
    attachmentsToAdd.length > 0 ||
    attachmentsToRemove.length > 0;

  function queueAttachments(nextFiles: File[]) {
    setAttachmentsToAdd((current) => [...current, ...nextFiles]);
    setError("");
  }

  function removePendingAttachment(target: File) {
    setAttachmentsToAdd((current) =>
      current.filter(
        (file) => !(file.name === target.name && file.lastModified === target.lastModified && file.size === target.size),
      ),
    );
  }

  function toggleRemoveAttachment(target: ProjectAttachment) {
    setAttachmentsToRemove((current) =>
      current.some((attachment) => attachment.storagePath === target.storagePath)
        ? current.filter((attachment) => attachment.storagePath !== target.storagePath)
        : [...current, target],
    );
  }

  async function handleSave() {
    if (!name.trim() || !description.trim() || !projectType.trim()) {
      setError("Name, description, and project type are required.");
      return;
    }

    setIsSaving(true);
    setError("");
    try {
      await updateProject({
        projectId: project.id,
        name: name.trim(),
        description: description.trim(),
        projectType: projectType.trim(),
        parcelDefinition,
        attachmentsToAdd,
        attachmentsToRemove,
      });
      setIsEditing(false);
    } catch (saveError) {
      console.error(saveError);
      setError("Project update failed. Check the parcel or attachment configuration.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="studio-project-details__backdrop" onClick={onClose}>
      <section
        className={`studio-project-details${isEditing ? " studio-project-details--editor" : ""}`}
        onClick={(event) => event.stopPropagation()}
        aria-label={`${project.name} details`}
      >
        <header className="studio-project-details__header">
          <div>
            <p className="studio-project-details__eyebrow">Project Details</p>
            <h2 className="studio-project-details__title">{isEditing ? "Edit project" : project.name}</h2>
          </div>
          <div className="studio-project-details__header-actions">
            {!isEditing ? (
              <Button type="button" variant="outline" className="studio-project-details__edit-button" onClick={() => setIsEditing(true)}>
                <Pencil size={14} />
                Edit
              </Button>
            ) : null}
            <button
              type="button"
              className="studio-project-details__close"
              onClick={onClose}
              aria-label="Close project details"
            >
              <X size={16} />
            </button>
          </div>
        </header>

        {isEditing ? (
          <>
            <div className="studio-project-details__warning studio-project-details__warning--global">
              <AlertTriangle size={16} />
              <span>Editing this project can change analysis inputs. Rerun analyses after saving if you update parcel data, radius, attachments, or project metadata.</span>
            </div>
            <div className="studio-project-details__content studio-project-details__content--editor">
              <div className="studio-project-details__form">
                <div className="studio-modal__field">
                  <Label htmlFor="project-details-name">Project name</Label>
                  <Input
                    id="project-details-name"
                    value={name}
                    onChange={(event) => {
                      setName(event.target.value);
                      setError("");
                    }}
                  />
                </div>

                <div className="studio-modal__field">
                  <Label htmlFor="project-details-type">Project type</Label>
                  <Select
                    value={projectType}
                    onValueChange={(value) => {
                      setProjectType(value);
                      setError("");
                    }}
                  >
                    <SelectTrigger id="project-details-type" className="w-full rounded-2xl">
                      <SelectValue placeholder="Select a project type" />
                    </SelectTrigger>
                    <SelectContent>
                      {PROJECT_TYPE_OPTIONS.map((option) => (
                        <SelectItem key={option} value={option}>
                          {option}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="studio-modal__field">
                  <Label htmlFor="project-details-description">Description</Label>
                  <Textarea
                    id="project-details-description"
                    value={description}
                    onChange={(event) => {
                      setDescription(event.target.value);
                      setError("");
                    }}
                    rows={4}
                  />
                </div>

                <div className="studio-project-details__section">
                  <div className="studio-project-details__section-header">
                    <p className="studio-project-details__label">Site parcel</p>
                    <span className="studio-project-details__helper">
                      Search, zoom, edit, and reposition the project boundary.
                    </span>
                  </div>
                  <SiteParcelMap
                    value={parcelDefinition}
                    onChange={setParcelDefinition}
                    wakeRadiusBoostMeters={50}
                  />
                </div>
              </div>

              <aside className="studio-project-details__sidebar">
                <div className="studio-project-details__section">
                  <div className="studio-project-details__section-header">
                    <p className="studio-project-details__label">Attachments</p>
                    <span className="studio-project-details__helper">
                      Add or remove project references.
                    </span>
                  </div>

                  <Input
                    id="project-details-attachments"
                    ref={fileInputRef}
                    className="sr-only"
                    type="file"
                    accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    multiple
                    onChange={(event) => {
                      const files = Array.from(event.target.files ?? []);
                      if (files.length > 0) queueAttachments(files);
                    }}
                  />

                  <button
                    type="button"
                    className={`studio-modal__dropzone${isDraggingAttachments ? " is-dragging" : ""}`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(event) => {
                      event.preventDefault();
                      setIsDraggingAttachments(true);
                    }}
                    onDragLeave={(event) => {
                      if (event.currentTarget.contains(event.relatedTarget as Node | null)) return;
                      setIsDraggingAttachments(false);
                    }}
                    onDrop={(event) => {
                      event.preventDefault();
                      setIsDraggingAttachments(false);
                      const files = Array.from(event.dataTransfer.files ?? []).filter((file) =>
                        /\.(pdf|docx)$/i.test(file.name),
                      );
                      if (files.length > 0) queueAttachments(files);
                    }}
                  >
                    <span className="studio-modal__dropzone-icon">
                      <Upload size={20} />
                    </span>
                    <span className="studio-modal__dropzone-copy">
                      <span className="studio-modal__dropzone-title">Drop files to update project context</span>
                      <span className="studio-modal__dropzone-text">PDF and DOCX are supported.</span>
                    </span>
                    <span className="studio-modal__dropzone-action">Add files</span>
                  </button>

                  <div className="studio-project-details__attachment-list">
                    {project.attachments.length === 0 && attachmentsToAdd.length === 0 ? (
                      <p className="studio-modal__hint">No attachments imported yet.</p>
                    ) : null}

                    {project.attachments.map((attachment) => {
                      const isMarkedForRemoval = attachmentsToRemove.some(
                        (candidate) => candidate.storagePath === attachment.storagePath,
                      );

                      return (
                        <div
                          key={attachment.storagePath}
                          className={`studio-project-details__attachment-item${isMarkedForRemoval ? " studio-project-details__attachment-item--removed" : ""}`}
                        >
                          <div className="studio-project-details__attachment-copy">
                            <FileText size={15} />
                            <div>
                              <a href={attachment.url} target="_blank" rel="noreferrer" className="studio-project-details__attachment-link">
                                {attachment.name}
                              </a>
                              <p className="studio-project-details__attachment-meta">
                                {isMarkedForRemoval
                                  ? `Marked for removal, ${formatAttachmentSize(attachment.size)}`
                                  : formatAttachmentSize(attachment.size)}
                              </p>
                            </div>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="studio-project-details__attachment-action"
                            onClick={() => toggleRemoveAttachment(attachment)}
                            aria-label={`${isMarkedForRemoval ? "Restore" : "Remove"} ${attachment.name}`}
                          >
                            {isMarkedForRemoval ? <X size={15} /> : <Trash2 size={15} />}
                          </Button>
                        </div>
                      );
                    })}

                    {attachmentsToAdd.map((attachment) => (
                      <div
                        key={`${attachment.name}-${attachment.lastModified}`}
                        className="studio-project-details__attachment-item studio-project-details__attachment-item--pending"
                      >
                        <div className="studio-project-details__attachment-copy">
                          <FileText size={15} />
                          <div>
                            <span className="studio-project-details__attachment-link">{attachment.name}</span>
                            <p className="studio-project-details__attachment-meta">
                              Pending upload, {formatAttachmentSize(attachment.size)}
                            </p>
                          </div>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="studio-project-details__attachment-action"
                          onClick={() => removePendingAttachment(attachment)}
                          aria-label={`Remove pending ${attachment.name}`}
                        >
                          <X size={15} />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="studio-project-details__meta">
                  <div className="studio-project-details__section">
                    <p className="studio-project-details__label">Created</p>
                    <p className="studio-project-details__body">
                      {new Date(project.createdAt).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                  </div>

                  <div className="studio-project-details__section">
                    <p className="studio-project-details__label">Project ID</p>
                    <p className="studio-project-details__body studio-project-details__body--mono">
                      {project.id}
                    </p>
                  </div>
                </div>
              </aside>
            </div>

            {error ? <p className="studio-modal__error">{error}</p> : null}

            <div className="studio-modal__actions">
              <Button
                type="button"
                variant="outline"
                className="studio-modal__btn"
                onClick={() => {
                  resetDraftState();
                  setIsEditing(false);
                }}
              >
                Cancel
              </Button>
              <Button
                type="button"
                className="studio-modal__btn studio-modal__btn--primary"
                onClick={() => void handleSave()}
                disabled={!hasChanges || isSaving}
              >
                {isSaving ? "Saving..." : "Save changes"}
              </Button>
            </div>
          </>
        ) : (
          <div className="studio-project-details__content studio-project-details__content--viewer">
            <div className="studio-project-details__form">
              <div className="studio-project-details__section">
                <p className="studio-project-details__label">Project type</p>
                <p className="studio-project-details__body">{project.projectType || "Not set"}</p>
              </div>

              <div className="studio-project-details__section">
                <p className="studio-project-details__label">Description</p>
                <p className="studio-project-details__body">{project.description || "No description yet."}</p>
              </div>

              <div className="studio-project-details__section">
                <div className="studio-project-details__section-header">
                  <p className="studio-project-details__label">Site parcel</p>
                  <span className="studio-project-details__helper">
                    Review the project location and analysis radius before entering edit mode.
                  </span>
                </div>
                <SiteParcelMap
                  value={project.parcelDefinition}
                  onChange={() => undefined}
                  editable={false}
                  wakeRadiusBoostMeters={50}
                />
              </div>
            </div>

            <aside className="studio-project-details__sidebar">
              <div className="studio-project-details__section">
                <div className="studio-project-details__section-header">
                  <p className="studio-project-details__label">Attachments</p>
                  <span className="studio-project-details__helper">
                    Open source files or switch to edit mode to replace them.
                  </span>
                </div>
                <div className="studio-project-details__attachment-list">
                  {project.attachments.length === 0 ? (
                    <p className="studio-modal__hint">No attachments imported yet.</p>
                  ) : (
                    project.attachments.map((attachment) => (
                      <div key={attachment.storagePath} className="studio-project-details__attachment-item">
                        <div className="studio-project-details__attachment-copy">
                          <FileText size={15} />
                          <div>
                            <a href={attachment.url} target="_blank" rel="noreferrer" className="studio-project-details__attachment-link">
                              {attachment.name}
                            </a>
                            <p className="studio-project-details__attachment-meta">
                              {formatAttachmentSize(attachment.size)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="studio-project-details__meta">
                <div className="studio-project-details__section">
                  <p className="studio-project-details__label">Created</p>
                  <p className="studio-project-details__body">
                    {new Date(project.createdAt).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </p>
                </div>

                <div className="studio-project-details__section">
                  <p className="studio-project-details__label">Project ID</p>
                  <p className="studio-project-details__body studio-project-details__body--mono">
                    {project.id}
                  </p>
                </div>
              </div>
            </aside>
          </div>
        )}
      </section>
    </div>
  );
}
