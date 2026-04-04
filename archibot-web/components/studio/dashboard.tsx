"use client";

import { useRef, useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, FileText, FolderOpen, Loader2, Plus, Upload, Users, X } from "lucide-react";
import { SiteParcelMap } from "@/components/mapbox/site-parcel-map";
import { ProjectDetails } from "@/components/studio/project-details";
import { useStudio } from "@/components/studio/studio-context";
import { Project, ProjectParcel } from "@/components/studio/types";
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

export function DashboardPanel() {
  const { projects, teams, selectedProjectId } = useStudio();
  const recent = projects.slice(0, 4);

  return (
    <div className="studio-panel-page">
      <header className="studio-panel-page__header">
        <h1 className="studio-panel-page__title">Dashboard</h1>
        <p className="studio-panel-page__subtitle">Overview of your studio.</p>
      </header>

      {/* Stats row */}
      <div className="dash-stats">
        <div className="dash-stat">
          <FolderOpen size={18} strokeWidth={1.5} />
          <span className="dash-stat__value">{projects.length}</span>
          <span className="dash-stat__label">ongoing projects</span>
        </div>
        <div className="dash-stat">
          <Users size={18} strokeWidth={1.5} />
          <span className="dash-stat__value">{teams.length}</span>
          <span className="dash-stat__label">teams</span>
        </div>
        <div className="dash-stat">
          <Bot size={18} strokeWidth={1.5} />
          <span className="dash-stat__value">6</span>
          <span className="dash-stat__label">running agents</span>
        </div>
      </div>

      {/* Recent projects */}
      <section className="dash-section">
        <h2 className="dash-section__title">Recent projects</h2>
        {recent.length === 0 ? (
          <p className="dash-empty">No projects yet. Head to the Projects tab to create one.</p>
        ) : (
          <div className="studio-dashboard__grid">
            {recent.map((project) => (
              <div key={project.id} className="studio-project-card">
                {selectedProjectId === project.id ? (
                  <span className="studio-project-card__selected-badge" aria-label="Selected project">
                    <CheckCircle2 size={16} />
                  </span>
                ) : null}
                {project.analysisStatus === "running" && (
                  <span className="studio-project-card__analysis-badge" aria-label="Analysis running">
                    <Loader2 size={13} className="animate-spin" />
                    <span>Analyzing…</span>
                  </span>
                )}
                {!project.analysisUpToDate && project.analysisStatus !== "running" && (
                  <span className="studio-project-card__stale-badge" aria-label="Analysis out of date">
                    <AlertTriangle size={13} />
                    <span>Outdated</span>
                  </span>
                )}
                <span className="studio-project-card__name">{project.name}</span>
                {project.description && (
                  <span className="studio-project-card__desc">{project.description}</span>
                )}
                <span className="studio-project-card__meta">
                  {new Date(project.createdAt).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export function ProjectsPanel() {
  const { projects, addProject, selectedProjectId, selectProject } = useStudio();
  const [showAdd, setShowAdd] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [projectType, setProjectType] = useState<(typeof PROJECT_TYPE_OPTIONS)[number]>("Residential");
  const [customProjectType, setCustomProjectType] = useState("");
  const [parcelDefinition, setParcelDefinition] = useState<ProjectParcel | null>(null);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [error, setError] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [isDraggingAttachments, setIsDraggingAttachments] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  function updateAttachments(nextFiles: File[]) {
    setAttachments(nextFiles);
    if (error) setError("");
  }

  function closeCreateModal() {
    setShowAdd(false);
    setError("");
    setName("");
    setDesc("");
    setProjectType("Residential");
    setCustomProjectType("");
    setParcelDefinition(null);
    setAttachments([]);
    setIsDraggingAttachments(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleCreate() {
    const nextName = name.trim();
    const nextDescription = desc.trim();
    const nextProjectType = projectType === "Other" ? customProjectType.trim() : projectType;

    if (!nextName || !nextDescription || !nextProjectType) {
      setError("Name, description, and project type are required.");
      return;
    }

    try {
      setIsCreating(true);
      setError("");
      await addProject({
        name: nextName,
        description: nextDescription,
        projectType: nextProjectType,
        parcelDefinition,
        attachments,
      });
      closeCreateModal();
    } catch (createError) {
      console.error(createError);
      setError("Project creation failed. Check the attachment upload configuration.");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div className="studio-panel-page">
      <header className="studio-panel-page__header">
        <h1 className="studio-panel-page__title">Projects</h1>
        <p className="studio-panel-page__subtitle">Your active projects.</p>
      </header>

      <div className="studio-dashboard__grid">
        {projects.map((project) => (
          <button
            key={project.id}
            type="button"
            className="studio-project-card"
            onClick={() => {
              selectProject(project.id);
              setSelectedProject(project);
            }}
          >
            {selectedProjectId === project.id ? (
              <span className="studio-project-card__selected-badge" aria-label="Selected project">
                <CheckCircle2 size={16} />
              </span>
            ) : null}
            {project.analysisStatus === "running" && (
              <span className="studio-project-card__analysis-badge" aria-label="Analysis running">
                <Loader2 size={13} className="animate-spin" />
                <span>Analyzing…</span>
              </span>
            )}
            {!project.analysisUpToDate && project.analysisStatus !== "running" && (
              <span className="studio-project-card__stale-badge" aria-label="Analysis out of date">
                <AlertTriangle size={13} />
                <span>Outdated</span>
              </span>
            )}
            <span className="studio-project-card__name">{project.name}</span>
            {project.description && (
              <span className="studio-project-card__desc">{project.description}</span>
            )}
            <span className="studio-project-card__meta">
              {new Date(project.createdAt).toLocaleDateString()}
            </span>
          </button>
        ))}

        <button
          className="studio-project-card studio-project-card--add"
          onClick={() => setShowAdd(true)}
        >
          <Plus size={22} strokeWidth={1.5} />
          <span>New project</span>
        </button>
      </div>

      {showAdd && (
        <div className="studio-modal-overlay" onClick={closeCreateModal}>
          <div className="studio-modal" onClick={(e) => e.stopPropagation()}>
            <div className="studio-modal__header">
              <h2>New project</h2>
              <button className="studio-modal__close" onClick={closeCreateModal}>
                <X size={15} />
              </button>
            </div>

            <div className="studio-modal__field">
              <Label htmlFor="proj-name">Name</Label>
              <Input
                id="proj-name"
                autoFocus
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (error) setError("");
                }}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                placeholder="e.g. Residential Tower"
              />
            </div>

            <div className="studio-modal__field">
              <Label htmlFor="proj-type">Project type</Label>
              <div
                className={`studio-modal__field-row${
                  projectType === "Other" ? " studio-modal__field-row--split" : ""
                }`}
              >
                <Select
                  value={projectType}
                  onValueChange={(value) => {
                    setProjectType(value as (typeof PROJECT_TYPE_OPTIONS)[number]);
                    if (value !== "Other") setCustomProjectType("");
                    if (error) setError("");
                  }}
                >
                  <SelectTrigger id="proj-type" className="w-full rounded-2xl">
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
                {projectType === "Other" ? (
                  <Input
                    id="proj-type-custom"
                    value={customProjectType}
                    onChange={(event) => {
                      setCustomProjectType(event.target.value);
                      if (error) setError("");
                    }}
                    placeholder="Custom type"
                  />
                ) : null}
              </div>
            </div>

            <div className="studio-modal__field">
              <Label htmlFor="proj-desc">Description</Label>
              <Textarea
                id="proj-desc"
                value={desc}
                onChange={(e) => {
                  setDesc(e.target.value);
                  if (error) setError("");
                }}
                placeholder="Describe the project, site, and scope"
                rows={3}
              />
            </div>

            <div className="studio-modal__field">
              <Label>Parcel definition</Label>
              <SiteParcelMap value={parcelDefinition} onChange={setParcelDefinition} />
            </div>

            <div className="studio-modal__field">
              <Label htmlFor="proj-attachments">Import relevant attachments</Label>
              <Input
                id="proj-attachments"
                ref={fileInputRef}
                className="sr-only"
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                multiple
                onChange={(event) => {
                  const files = Array.from(event.target.files ?? []);
                  updateAttachments(files);
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
                  if (files.length > 0) updateAttachments(files);
                }}
              >
                <span className="studio-modal__dropzone-icon">
                  <Upload size={20} />
                </span>
                <span className="studio-modal__dropzone-copy">
                  <span className="studio-modal__dropzone-title">Drop PDF or DOCX files here</span>
                  <span className="studio-modal__dropzone-text">
                    Or browse from your device to seed the project context.
                  </span>
                </span>
                <span className="studio-modal__dropzone-action">Choose files</span>
              </button>
              {attachments.length > 0 ? (
                <div className="studio-modal__file-list">
                  {attachments.map((file) => (
                    <div key={`${file.name}-${file.lastModified}`} className="studio-modal__file-item">
                      <FileText size={14} />
                      <span>{file.name}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="studio-modal__hint">Accepted formats: PDF and DOCX.</p>
              )}
            </div>

            {error ? <p className="studio-modal__error">{error}</p> : null}

            <div className="studio-modal__actions">
              <Button variant="outline" className="studio-modal__btn" onClick={closeCreateModal}>
                Cancel
              </Button>
              <Button
                className="studio-modal__btn studio-modal__btn--primary"
                onClick={handleCreate}
                disabled={!name.trim() || !desc.trim() || !(projectType === "Other" ? customProjectType.trim() : projectType) || isCreating}
              >
                {isCreating ? "Creating..." : "Create"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {selectedProject && (
        <ProjectDetails
          project={selectedProject}
          onClose={() => setSelectedProject(null)}
        />
      )}
    </div>
  );
}
