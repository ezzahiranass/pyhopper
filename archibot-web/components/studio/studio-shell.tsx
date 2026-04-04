"use client";

import { StudioProvider, useStudio } from "@/components/studio/studio-context";
import { Sidebar } from "@/components/studio/sidebar";
import { OrgChartEditor } from "@/components/studio/org-chart-editor";
import { DashboardPanel, ProjectsPanel } from "@/components/studio/dashboard";
import { StudioSettingsPanel } from "@/components/studio/settings-panel";
import { StudioPlayground } from "@/components/studio/studio-playground";
import { ChatApp } from "@/components/chatapp/chat-app";
import { WorkspaceApp } from "@/components/workspace/workspace-app";
import { NotificationTray } from "@/components/ui/notification";

function Placeholder({ label, hint }: { label: string; hint?: string }) {
  return (
    <div className="studio-placeholder">
      <p>{label}</p>
      <span>{hint ?? "Coming soon"}</span>
    </div>
  );
}

function TeamTab() {
  const { teams, activeTeamId, updateTeamOrgChart } = useStudio();
  const activeTeam = teams.find((t) => t.id === activeTeamId);

  if (!activeTeam) {
    return <Placeholder label="No team selected" hint="Use the sidebar to select or create a team." />;
  }

  return (
    <OrgChartEditor
      items={activeTeam.orgChart}
      onItemsChange={(items) => updateTeamOrgChart(activeTeam.id, items)}
      onSelectionChange={() => {}}
    />
  );
}

function StudioContent() {
  const { activeTab, activeTeamId, loading } = useStudio();

  if (loading) {
    return (
      <main className="studio-main">
        <Placeholder label="" hint="Loading..." />
      </main>
    );
  }

  if (activeTab === "settings") {
    return (
      <main className="studio-main">
        <StudioSettingsPanel />
      </main>
    );
  }

  if (activeTab === "playground") {
    return (
      <main className="studio-main">
        <StudioPlayground />
      </main>
    );
  }

  // Gate all content on having an active team
  if (!activeTeamId) {
    return (
      <main className="studio-main">
        <Placeholder label="No team selected" hint="Select or create a team from the sidebar to get started." />
      </main>
    );
  }

  return (
    <main className="studio-main">
      {activeTab === "dashboard" && <DashboardPanel />}
      {activeTab === "team" && <TeamTab />}
      {activeTab === "projects" && <ProjectsPanel />}
      {activeTab === "conversation" && <ChatApp />}
      {activeTab === "workspace" && <WorkspaceApp />}
    </main>
  );
}

function StudioInner() {
  const { notifications, dismissNotification } = useStudio();
  return (
    <div className="studio-layout">
      <Sidebar />
      <StudioContent />
      <NotificationTray notifications={notifications} onDismiss={dismissNotification} />
    </div>
  );
}

export function StudioShell({ children }: { children?: React.ReactNode }) {
  return (
    <StudioProvider>
      <StudioInner />
      {children}
    </StudioProvider>
  );
}
