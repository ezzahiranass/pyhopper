"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { useStudio } from "@/components/studio/studio-context";
import { ChatSidebar } from "./chat-sidebar";
import { ChatView } from "./chat-view";
import {
  createChannelConversation,
  deleteConversation,
  createGroupConversation,
  createOrGetDmConversation,
  makeParticipantRef,
  renameConversation,
  subscribeProjectConversations,
  subscribeProjectParticipants,
  subscribeResolvedParticipants,
  updateConversationParticipants,
  type Conversation,
  type ParticipantRef,
  type ResolvedParticipant,
} from "./chat-service";

export function ChatApp() {
  const { user } = useAuth();
  const { projects, activeTeamId, selectedProjectId: activeProjectId, selectProject } = useStudio();
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [conversationState, setConversationState] = useState<{
    projectId: string | null;
    items: Conversation[];
  }>({
    projectId: null,
    items: [],
  });
  const [participantState, setParticipantState] = useState<{
    projectId: string | null;
    items: ResolvedParticipant[];
  }>({
    projectId: null,
    items: [],
  });
  const [activeParticipantState, setActiveParticipantState] = useState<{
    conversationId: string | null;
    items: ResolvedParticipant[];
  }>({
    conversationId: null,
    items: [],
  });

  const currentUserRef = user ? makeParticipantRef("user", user.uid) : null;
  const currentUserName = user?.displayName ?? user?.email ?? "You";

  useEffect(() => {
    if (!activeProjectId) return;
    return subscribeProjectConversations(activeProjectId, (items) => {
      setConversationState({ projectId: activeProjectId, items });
    });
  }, [activeProjectId]);

  useEffect(() => {
    if (!activeProjectId || !user) return;
    return subscribeProjectParticipants(activeProjectId, user.uid, (items) => {
      setParticipantState({ projectId: activeProjectId, items });
    });
  }, [activeProjectId, user]);

  const conversations = useMemo(
    () => (activeProjectId === conversationState.projectId ? conversationState.items : []),
    [activeProjectId, conversationState],
  );
  const eligibleParticipants = useMemo(
    () => (activeProjectId === participantState.projectId ? participantState.items : []),
    [activeProjectId, participantState],
  );

  const activeConversation = useMemo(() => {
    if (conversations.length === 0) return null;

    if (selectedConversationId) {
      return conversations.find((conversation) => conversation.id === selectedConversationId) ?? null;
    }

    return conversations[0] ?? null;
  }, [conversations, selectedConversationId]);

  useEffect(() => {
    if (!activeConversation) return;

    return subscribeResolvedParticipants(activeConversation.participantIds, (items) => {
      setActiveParticipantState({ conversationId: activeConversation.id, items });
    });
  }, [activeConversation]);

  const groupedConversations = useMemo(() => ({
    channels: conversations.filter((conversation) => conversation.kind === "channel"),
    groups: conversations.filter((conversation) => conversation.kind === "group"),
    dms: conversations.filter((conversation) => conversation.kind === "dm"),
  }), [conversations]);

  const activeDmTargetRef = useMemo(() => {
    if (!activeConversation || activeConversation.kind !== "dm" || !currentUserRef) return null;

    return (
      activeConversation.participantIds.find((participantRef) => participantRef !== currentUserRef) ??
      activeConversation.participantIds[0] ??
      null
    );
  }, [activeConversation, currentUserRef]);

  const activeParticipants = useMemo(
    () => (activeConversation?.id === activeParticipantState.conversationId ? activeParticipantState.items : []),
    [activeConversation?.id, activeParticipantState],
  );

  const activeTitle = useMemo(() => {
    if (!activeConversation) return null;

    if (activeConversation.kind === "dm") {
      const peer = activeParticipants.find((participant) => participant.ref !== currentUserRef);
      return peer?.label ?? "Direct message";
    }

    return activeConversation.title ?? "Untitled conversation";
  }, [activeConversation, activeParticipants, currentUserRef]);

  async function handleAddChannel(name: string) {
    if (!activeProjectId || !currentUserRef) return;

    const conversation = await createChannelConversation(
      activeProjectId,
      name,
      [currentUserRef, ...eligibleParticipants.map((participant) => participant.ref)],
      currentUserRef,
    );

    setSelectedConversationId(conversation.id);
  }

  async function handleOpenDm(participantRef: ParticipantRef) {
    if (!activeProjectId || !currentUserRef) return;

    const conversation = await createOrGetDmConversation(
      activeProjectId,
      [currentUserRef, participantRef],
      currentUserRef,
    );

    setSelectedConversationId(conversation.id);
  }

  async function handleAddGroup(name: string) {
    if (!activeProjectId || !currentUserRef) return;

    const conversation = await createGroupConversation(
      activeProjectId,
      name,
      [currentUserRef],
      currentUserRef,
    );

    setSelectedConversationId(conversation.id);
  }

  async function handleUpdateGroupParticipants(conversationId: string, participantRefs: ParticipantRef[]) {
    if (!currentUserRef) return;
    await updateConversationParticipants(conversationId, [currentUserRef, ...participantRefs]);
  }

  async function handleRenameConversation(conversationId: string, title: string) {
    await renameConversation(conversationId, title);
  }

  async function handleDeleteConversation(conversation: Conversation) {
    await deleteConversation(conversation);
    setSelectedConversationId((current) => (current === conversation.id ? null : current));
  }

  function handleSelectProject(id: string) {
    selectProject(id);
    setSelectedConversationId(null);
  }

  return (
    <div className="chat-app">
      <ChatSidebar
        projects={projects}
        activeProjectId={activeProjectId}
        onSelectProject={handleSelectProject}
        channels={groupedConversations.channels}
        groups={groupedConversations.groups}
        dmConversations={groupedConversations.dms}
        members={eligibleParticipants}
        activeConversationId={activeConversation?.id ?? null}
        activeDmTargetRef={activeDmTargetRef}
        currentUserRef={currentUserRef}
        onSelectConversation={setSelectedConversationId}
        onOpenDm={handleOpenDm}
        onAddChannel={handleAddChannel}
        onAddGroup={handleAddGroup}
      />

      {activeConversation && currentUserRef && activeTitle ? (
        <ChatView
          key={activeConversation.id}
          conversation={activeConversation}
          participants={activeParticipants}
          mentionParticipants={eligibleParticipants}
          title={activeTitle}
          currentUserRef={currentUserRef}
          currentUserName={currentUserName}
          teamId={activeTeamId ?? ""}
          onUpdateGroupParticipants={handleUpdateGroupParticipants}
          onRenameConversation={handleRenameConversation}
          onDeleteConversation={handleDeleteConversation}
        />
      ) : (
        <div className="chat-view chat-view--empty">
          <p>
            {!activeProjectId
              ? "Select a project to start chatting."
              : "Create or open a conversation."}
          </p>
        </div>
      )}
    </div>
  );
}
