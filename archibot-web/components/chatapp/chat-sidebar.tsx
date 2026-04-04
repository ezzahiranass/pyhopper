"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, Hash, Plus, Users } from "lucide-react";
import type { Project } from "@/components/studio/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getConversationUnreadCount,
  type Conversation,
  type ParticipantRef,
  type ResolvedParticipant,
} from "./chat-service";

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

interface ChatSidebarProps {
  projects: Project[];
  activeProjectId: string | null;
  onSelectProject: (id: string) => void;
  channels: Conversation[];
  groups: Conversation[];
  dmConversations: Conversation[];
  members: ResolvedParticipant[];
  activeConversationId: string | null;
  activeDmTargetRef: ParticipantRef | null;
  currentUserRef: ParticipantRef | null;
  onSelectConversation: (conversationId: string) => void;
  onOpenDm: (participantRef: ParticipantRef) => void | Promise<void>;
  onAddChannel: (name: string) => void | Promise<void>;
  onAddGroup: (name: string) => void | Promise<void>;
}

function participantInitials(participant: ResolvedParticipant) {
  const parts = participant.label.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return participant.label.slice(0, 2).toUpperCase();
}

function jobInitials(label: string | null) {
  if (!label) return null;

  const words = label
    .split(/[\s-]+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (words.length === 0) return null;
  if (words.length === 1) return words[0][0].toUpperCase();

  return words.map((word) => `${word[0].toUpperCase()}.`).join("");
}

export function ChatSidebar({
  projects,
  activeProjectId,
  onSelectProject,
  channels,
  groups,
  dmConversations,
  members,
  activeConversationId,
  activeDmTargetRef,
  currentUserRef,
  onSelectConversation,
  onOpenDm,
  onAddChannel,
  onAddGroup,
}: ChatSidebarProps) {
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [creatingGroup, setCreatingGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");

  async function handleCreate() {
    const trimmed = newName.trim();
    if (!trimmed) return;
    await onAddChannel(trimmed);
    setNewName("");
    setCreating(false);
  }

  async function handleCreateGroup() {
    const trimmed = newGroupName.trim();
    if (!trimmed) return;
    await onAddGroup(trimmed);
    setNewGroupName("");
    setCreatingGroup(false);
  }

  const dmConversationByTargetRef = new Map<ParticipantRef, Conversation>();

  if (currentUserRef) {
    for (const conversation of dmConversations) {
      const targetRef =
        conversation.participantIds.find((participantRef) => participantRef !== currentUserRef) ??
        conversation.participantIds[0] ??
        null;
      if (targetRef) {
        dmConversationByTargetRef.set(targetRef, conversation);
      }
    }
  }

  return (
    <aside className="chat-sidebar">
      <div className="chat-sidebar__header">
        <ProjectPicker
          projects={projects}
          activeProjectId={activeProjectId}
          onSelect={onSelectProject}
        />
      </div>

      <nav className="chat-sidebar__nav">
        <p className="chat-sidebar__section-label">Channels</p>
        {channels.map((conversation) => (
          (() => {
            const unreadCount = currentUserRef ? getConversationUnreadCount(conversation, currentUserRef) : 0;
            return (
              <button
                key={conversation.id}
                className={`chat-sidebar__item${activeConversationId === conversation.id ? " active" : ""}`}
                onClick={() => onSelectConversation(conversation.id)}
              >
                <Hash size={14} strokeWidth={2.5} className="chat-sidebar__hash-icon" />
                <span className="chat-sidebar__item-name">{conversation.title ?? "Untitled channel"}</span>
                {conversation.typingParticipantRefs.length > 0 ? (
                  <span className="chat-sidebar__typing" aria-label="Agents are typing">
                    <span className="chat-sidebar__typing-dot" />
                    <span className="chat-sidebar__typing-dot" />
                    <span className="chat-sidebar__typing-dot" />
                  </span>
                ) : null}
                {unreadCount > 0 ? (
                  <span className="chat-sidebar__unread-badge">{unreadCount}</span>
                ) : null}
              </button>
            );
          })()
        ))}

        {creating ? (
          <div className="chat-sidebar__create">
            <Input
              autoFocus
              value={newName}
              onChange={(event) => setNewName(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void handleCreate();
                if (event.key === "Escape") {
                  setCreating(false);
                  setNewName("");
                }
              }}
              placeholder="Channel name"
            />
            <Button
              size="sm"
              className="chat-sidebar__create-btn"
              onClick={() => void handleCreate()}
              disabled={!newName.trim()}
            >
              Add
            </Button>
          </div>
        ) : (
          <button
            className="chat-sidebar__item chat-sidebar__item--add"
            onClick={() => setCreating(true)}
          >
            <Plus size={14} />
            <span>Add channel</span>
          </button>
        )}

        <p className="chat-sidebar__section-label chat-sidebar__section-label--spaced">
          Group Chats
        </p>
        {groups.length === 0 ? (
          <p className="chat-sidebar__empty">No group chats yet.</p>
        ) : (
          groups.map((conversation) => (
            (() => {
              const unreadCount = currentUserRef ? getConversationUnreadCount(conversation, currentUserRef) : 0;
              return (
                <button
                  key={conversation.id}
                  className={`chat-sidebar__item${activeConversationId === conversation.id ? " active" : ""}`}
                  onClick={() => onSelectConversation(conversation.id)}
                >
                  <Users size={14} className="chat-sidebar__hash-icon" />
                  <span className="chat-sidebar__item-name">{conversation.title ?? "Untitled group"}</span>
                  {conversation.typingParticipantRefs.length > 0 ? (
                    <span className="chat-sidebar__typing" aria-label="Agents are typing">
                      <span className="chat-sidebar__typing-dot" />
                      <span className="chat-sidebar__typing-dot" />
                      <span className="chat-sidebar__typing-dot" />
                    </span>
                  ) : null}
                  {unreadCount > 0 ? (
                    <span className="chat-sidebar__unread-badge">{unreadCount}</span>
                  ) : null}
                </button>
              );
            })()
          ))
        )}
        {creatingGroup ? (
          <div className="chat-sidebar__create chat-sidebar__create--group">
            <Input
              autoFocus
              value={newGroupName}
              onChange={(event) => setNewGroupName(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  setCreatingGroup(false);
                  setNewGroupName("");
                }
              }}
              placeholder="Group chat name"
            />
            <Button
              size="sm"
              className="chat-sidebar__create-btn chat-sidebar__create-btn--wide"
              onClick={() => void handleCreateGroup()}
              disabled={!newGroupName.trim()}
            >
              Add
            </Button>
          </div>
        ) : (
          <button
            className="chat-sidebar__item chat-sidebar__item--add"
            onClick={() => setCreatingGroup(true)}
          >
            <Plus size={14} />
            <span>Add group chat</span>
          </button>
        )}

        <p className="chat-sidebar__section-label chat-sidebar__section-label--spaced">
          Direct Messages
        </p>
        {members.length === 0 ? (
          <p className="chat-sidebar__empty">No project members available.</p>
        ) : (
          members.map((member) => (
            (() => {
              const conversation = dmConversationByTargetRef.get(member.ref) ?? null;
              const unreadCount =
                conversation && currentUserRef ? getConversationUnreadCount(conversation, currentUserRef) : 0;

              return (
                <button
                  key={member.ref}
                  className={`chat-sidebar__item chat-sidebar__item--dm${activeDmTargetRef === member.ref ? " active" : ""}`}
                  onClick={() => void onOpenDm(member.ref)}
                  title={member.description ?? member.secondaryLabel ?? undefined}
                >
                  <span className="chat-sidebar__dm-avatar">{participantInitials(member)}</span>
                  {member.kind === "agent" ? (
                    <span className="chat-sidebar__dm-copy">
                      <span className="chat-sidebar__dm-default">
                        <span className="chat-sidebar__item-name">{member.label}</span>
                        <span className="chat-sidebar__member-meta">
                          {jobInitials(member.secondaryLabel) ?? "A"}
                        </span>
                      </span>
                      <span className="chat-sidebar__dm-hover-title">
                        {member.secondaryLabel ?? member.label}
                      </span>
                    </span>
                  ) : (
                    <span className="chat-sidebar__dm-copy">
                      <span className="chat-sidebar__item-name">{member.label}</span>
                      <span className="chat-sidebar__member-meta">U</span>
                    </span>
                  )}
                  {conversation?.typingParticipantRefs.length ? (
                    <span className="chat-sidebar__typing" aria-label="Agents are typing">
                      <span className="chat-sidebar__typing-dot" />
                      <span className="chat-sidebar__typing-dot" />
                      <span className="chat-sidebar__typing-dot" />
                    </span>
                  ) : null}
                  {unreadCount > 0 ? (
                    <span className="chat-sidebar__unread-badge">{unreadCount}</span>
                  ) : null}
                </button>
              );
            })()
          ))
        )}
      </nav>
    </aside>
  );
}
