"use client";

import { useState } from "react";
import { Info, X } from "lucide-react";
import { OrgChartItem, Project } from "@/components/studio/types";

type Props = {
  project: Project;
  selectedNode: OrgChartItem | null;
};

export function InfoPanel({ project, selectedNode }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        className="studio-info-fab"
        onClick={() => setOpen((o) => !o)}
        aria-label="Toggle info panel"
        data-active={open ? "true" : "false"}
      >
        <Info size={16} />
      </button>

      {open && (
        <div className="studio-info-panel">
          <div className="studio-info-panel__header">
            <span>{selectedNode ? "Node Information" : "Project Information"}</span>
            <button className="studio-info-panel__close" onClick={() => setOpen(false)}>
              <X size={14} />
            </button>
          </div>

          <div className="studio-info-panel__body">
            {selectedNode ? (
              <>
                <p className="studio-info-panel__label">Name</p>
                <p className="studio-info-panel__value">{selectedNode.name}</p>
                <p className="studio-info-panel__label">Job</p>
                <p className="studio-info-panel__value">{selectedNode.job}</p>
                <p className="studio-info-panel__label">Description</p>
                <p className="studio-info-panel__value">{selectedNode.description}</p>
                <p className="studio-info-panel__label">Personality</p>
                <p className="studio-info-panel__value">{selectedNode.personality || "Default"}</p>
                <p className="studio-info-panel__label">Type</p>
                <p className="studio-info-panel__value">
                  {selectedNode.parentId === null ? "Root role" : "Team role"}
                </p>
              </>
            ) : (
              <>
                <p className="studio-info-panel__label">Project</p>
                <p className="studio-info-panel__value">{project.name}</p>
                {project.description && (
                  <>
                    <p className="studio-info-panel__label">Description</p>
                    <p className="studio-info-panel__value">{project.description}</p>
                  </>
                )}
                <p className="studio-info-panel__label">Created</p>
                <p className="studio-info-panel__value">
                  {new Date(project.createdAt).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
