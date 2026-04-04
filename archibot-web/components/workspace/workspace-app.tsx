"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import {
  getConversationUnreadCount,
  makeParticipantRef,
  subscribeProjectConversations,
  type Conversation,
} from "@/components/chatapp/chat-service";
import { useStudio } from "@/components/studio/studio-context";
import { WorkspaceArtifactViewerProvider } from "@/components/workspace/artifacts/artifact-viewer-context";
import { InfiniteBoard } from "@/components/workspace/infinite-board";
import { WorkspaceSidebar } from "@/components/workspace/workspace-sidebar";
import { useProjectWorkspace } from "@/components/workspace/workspace-store";

export function WorkspaceApp() {
  const { user } = useAuth();
  const {
    projects,
    teams,
    activeTeamId,
    activeProject,
    selectedProjectId,
    selectProject,
    runAnalysis,
    settings,
  } = useStudio();
  const {
    areas,
    loading,
    persistAreaDelta,
    persistAreaFrame,
    persistSubdomainLayout,
    createArea,
    createSubdomain,
    updateAreaMetadata,
    updateSubdomainMetadata,
    deleteArea,
    deleteSubdomain,
  } = useProjectWorkspace(activeProject?.id ?? null);
  const [conversationState, setConversationState] = useState<{
    projectId: string | null;
    items: Conversation[];
  }>({
    projectId: null,
    items: [],
  });
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [activeItemId, setActiveItemId] = useState<string | null>(null);
  const [focusRequestKey, setFocusRequestKey] = useState(0);
  const currentUserRef = user ? makeParticipantRef("user", user.uid) : null;
  const activeTeam = useMemo(
    () => teams.find((team) => team.id === activeTeamId) ?? null,
    [activeTeamId, teams],
  );
  const activeProjectId = activeProject?.id ?? null;

  useEffect(() => {
    if (!activeProjectId) return;

    return subscribeProjectConversations(activeProjectId, (items) => {
      setConversationState({ projectId: activeProjectId, items });
    });
  }, [activeProjectId]);

  const projectConversations = useMemo(
    () => (activeProjectId && conversationState.projectId === activeProjectId ? conversationState.items : []),
    [activeProjectId, conversationState],
  );
  const agentChatStatus = useMemo(() => {
    const statuses = Object.fromEntries(
      (activeTeam?.orgChart ?? []).map((agent) => [
        agent.id,
        { isTyping: false, unreadCount: 0 },
      ]),
    ) as Record<string, { isTyping: boolean; unreadCount: number }>;

    if (!currentUserRef) return statuses;

    for (const conversation of projectConversations) {
      for (const typingRef of conversation.typingParticipantRefs) {
        if (!typingRef.startsWith("agent:")) continue;
        const agentId = typingRef.slice("agent:".length);
        if (statuses[agentId]) {
          statuses[agentId].isTyping = true;
        }
      }

      if (conversation.kind !== "dm") continue;

      const targetRef =
        conversation.participantIds.find((participantRef) => participantRef !== currentUserRef) ??
        conversation.participantIds[0] ??
        null;

      if (!targetRef || !targetRef.startsWith("agent:")) continue;
      const agentId = targetRef.slice("agent:".length);
      if (!statuses[agentId]) continue;
      statuses[agentId].unreadCount = getConversationUnreadCount(conversation, currentUserRef);
    }

    return statuses;
  }, [activeTeam?.orgChart, currentUserRef, projectConversations]);
  const resolvedSectionId =
    activeSectionId && areas.some((area) => area.id === activeSectionId)
      ? activeSectionId
      : areas[0]?.id ?? null;
  const resolvedArea = resolvedSectionId ? areas.find((area) => area.id === resolvedSectionId) ?? null : null;
  const resolvedItemId =
    activeItemId && resolvedArea?.subdomains.some((item) => item.id === activeItemId)
      ? activeItemId
      : null;

  function handleSelectSection(id: string) {
    setActiveSectionId(id);
    setActiveItemId(null);
    setFocusRequestKey((current) => current + 1);
  }

  function handleSelectItem(sectionId: string, itemId: string) {
    setActiveSectionId(sectionId);
    setActiveItemId(itemId);
    setFocusRequestKey((current) => current + 1);
  }

  return (
    <WorkspaceArtifactViewerProvider
      key={activeProject?.id ?? "workspace-empty"}
      optimizeEmbeds={settings.optimizeCanvasEmbeds}
    >
      <div className="workspace-app">
        <WorkspaceSidebar
          projects={projects}
          areas={areas}
          activeProjectId={selectedProjectId}
          onSelectProject={selectProject}
          activeSectionId={resolvedSectionId}
          activeItemId={resolvedItemId}
          onSelectSection={handleSelectSection}
          onSelectItem={handleSelectItem}
        />
        {activeProject && !loading && areas.length > 0 ? (
          <InfiniteBoard
            key={activeProject.id}
            project={activeProject}
            areas={areas}
            onPersistAreaDelta={persistAreaDelta}
            onPersistAreaFrame={persistAreaFrame}
            onPersistSubdomainLayout={persistSubdomainLayout}
            onCreateArea={createArea}
            onCreateSubdomain={createSubdomain}
            onUpdateAreaMetadata={updateAreaMetadata}
            onUpdateSubdomainMetadata={updateSubdomainMetadata}
            onDeleteArea={deleteArea}
            onDeleteSubdomain={deleteSubdomain}
            agents={activeTeam?.orgChart ?? []}
            agentChatStatus={agentChatStatus}
            focusedSectionId={resolvedSectionId}
            focusedItemId={resolvedItemId}
            focusRequestKey={focusRequestKey}
            onRunAnalysis={() => runAnalysis(activeProject.id)}
            analysisUpToDate={activeProject.analysisUpToDate}
          />
        ) : (
          <div className="workspace-board workspace-board--empty">
            <div className="workspace-board__empty-state">
              <span>{activeProject ? "Loading workspace..." : "Select a project to open its workspace."}</span>
            </div>
          </div>
        )}
      </div>
    </WorkspaceArtifactViewerProvider>
  );
}
