"use client";

import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useStudio } from "@/components/studio/studio-context";
import { OrgChartEditor } from "@/components/studio/org-chart-editor";
import { InfoPanel } from "@/components/studio/info-panel";
import { OrgChartItem } from "@/components/studio/types";

type ProjectTab = "orgchart" | "conversation";

export function ProjectView() {
  const { projects, teams, activeTeamId, selectTeam, updateTeamOrgChart } = useStudio();
  const activeTeam = teams.find((team) => team.id === activeTeamId) ?? null;
  const project = projects[0] ?? null;
  const [tab, setTab] = useState<ProjectTab>("orgchart");
  const [selectedNode, setSelectedNode] = useState<OrgChartItem | null>(null);

  if (!activeTeam || !project) return null;

  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh", overflow: "hidden" }}>
      {tab === "orgchart" ? (
        <OrgChartEditor
          items={activeTeam.orgChart}
          onItemsChange={(items) => updateTeamOrgChart(activeTeam.id, items)}
          onSelectionChange={setSelectedNode}
        />
      ) : (
        <div className="studio-conversation-placeholder">
          <p>Conversation</p>
          <span>Coming soon</span>
        </div>
      )}

      <div className="studio-project-top-left">
        <button
          className="studio-topbar-icon-btn"
          onClick={() => activeTeamId && selectTeam(activeTeamId)}
          aria-label="Back to dashboard"
        >
          <ArrowLeft size={16} />
        </button>
        <InfoPanel project={project} selectedNode={selectedNode} />
      </div>

      <div className="studio-view-switch">
        <button
          className={tab === "orgchart" ? "active" : ""}
          onClick={() => setTab("orgchart")}
        >
          Org Chart
        </button>
        <button
          className={tab === "conversation" ? "active" : ""}
          onClick={() => setTab("conversation")}
        >
          Conversation
        </button>
      </div>
    </div>
  );
}
