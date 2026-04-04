"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, FolderOpen } from "lucide-react";
import type { Project, WorkspaceArea } from "@/components/studio/types";

type WorkspaceSidebarProps = {
  projects: Project[];
  areas: WorkspaceArea[];
  activeProjectId: string | null;
  onSelectProject: (id: string) => void;
  activeSectionId: string | null;
  activeItemId: string | null;
  onSelectSection: (id: string) => void;
  onSelectItem: (sectionId: string, itemId: string) => void;
};

function ProjectPicker({
  projects,
  activeProjectId,
  onSelect,
}: {
  projects: Project[];
  activeProjectId: string | null;
  onSelect: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const active = projects.find((project) => project.id === activeProjectId);

  useEffect(() => {
    function handler(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div className="sidebar-team" ref={ref}>
      <button
        className="sidebar-team__trigger"
        onClick={() => setOpen((current) => !current)}
      >
        <span className="sidebar-team__name">
          {active?.name ?? "Select a project"}
        </span>
        <ChevronDown
          size={13}
          className={open ? "sidebar-team__chevron--open" : ""}
        />
      </button>

      {open && (
        <div className="sidebar-team__dropdown">
          {projects.length === 0 && (
            <p className="sidebar-team__empty">No projects yet.</p>
          )}
          {projects.map((project) => (
            <button
              key={project.id}
              className={`sidebar-team__option${project.id === activeProjectId ? " active" : ""}`}
              onClick={() => {
                onSelect(project.id);
                setOpen(false);
              }}
            >
              <span>{project.name}</span>
              {project.id === activeProjectId && <Check size={13} />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function WorkspaceSidebar({
  projects,
  areas,
  activeProjectId,
  onSelectProject,
  activeSectionId,
  activeItemId,
  onSelectSection,
  onSelectItem,
}: WorkspaceSidebarProps) {
  const [openSectionState, setOpenSectionState] = useState<Record<string, boolean>>({});

  function toggleSection(id: string) {
    setOpenSectionState((current) => ({
      ...current,
      [id]: !(current[id] ?? true),
    }));
  }

  return (
    <aside className="chat-sidebar workspace-sidebar">
      <div className="chat-sidebar__header">
        <ProjectPicker
          projects={projects}
          activeProjectId={activeProjectId}
          onSelect={onSelectProject}
        />
      </div>

      <nav className="chat-sidebar__nav">
        {areas.map((section, index) => {
          const isOpen = openSectionState[section.id] ?? true;

          return (
            <div key={section.id} className="workspace-sidebar__group">
              <div
                className={`chat-sidebar__item workspace-sidebar__section-row${activeSectionId === section.id ? " active" : ""}`}
              >
                <button
                  type="button"
                  className="workspace-sidebar__section-trigger"
                  onClick={() => onSelectSection(section.id)}
                >
                  <FolderOpen size={14} strokeWidth={2.2} className="chat-sidebar__hash-icon" />
                  <span className="chat-sidebar__item-name">{section.name}</span>
                  <span className="chat-sidebar__member-meta">{section.type}</span>
                </button>
                <button
                  type="button"
                  className={`workspace-sidebar__toggle${isOpen ? " is-open" : ""}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    toggleSection(section.id);
                  }}
                  aria-label={isOpen ? `Collapse ${section.name}` : `Expand ${section.name}`}
                >
                  <ChevronDown size={13} className="workspace-sidebar__chevron" />
                </button>
              </div>

              {isOpen ? (
                <div className="workspace-sidebar__items">
                  {section.subdomains.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={`chat-sidebar__item workspace-sidebar__leaf${activeItemId === item.id ? " active" : ""}`}
                      onClick={() => onSelectItem(section.id, item.id)}
                    >
                      <span className="workspace-sidebar__index">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span className="chat-sidebar__item-name">{item.name}</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
