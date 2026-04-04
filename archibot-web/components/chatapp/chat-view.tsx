"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Plus, Settings2, Square, Trash2, Users, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
  clearConversationRuntime,
  continueConversationModeratorLoop,
  dismissConversationModeratorLoop,
  sendConversationDraft,
  stopConversationRuntime,
  useConversationRuntime,
} from "./chat-runtime";
import { Message, StreamingMessage, TypingMessage } from "./message";
import {
  clearConversationHistory,
  deleteConversationMessage,
  getConversationUnreadCount,
  markConversationSeen,
  subscribeConversationMessages,
  updateConversationMessage,
  type ChatMessage,
  type Conversation,
  type ParticipantRef,
  type ResolvedParticipant,
} from "./chat-service";

type ChatViewProps = {
  conversation: Conversation;
  participants: ResolvedParticipant[];
  mentionParticipants: ResolvedParticipant[];
  title: string;
  currentUserRef: ParticipantRef;
  currentUserName: string;
  teamId: string;
  onUpdateGroupParticipants?: (conversationId: string, participantRefs: ParticipantRef[]) => void | Promise<void>;
  onRenameConversation?: (conversationId: string, title: string) => void | Promise<void>;
  onDeleteConversation?: (conversation: Conversation) => void | Promise<void>;
};

type MentionMatch = {
  start: number;
  end: number;
  query: string;
};

const MAX_MENTION_OPTIONS = 6;

function getActiveMention(value: string, caretIndex: number): MentionMatch | null {
  const safeCaret = Math.max(0, Math.min(caretIndex, value.length));
  const prefix = value.slice(0, safeCaret);
  const mentionStart = prefix.lastIndexOf("@");

  if (mentionStart < 0) return null;
  if (mentionStart > 0 && !/\s/.test(prefix[mentionStart - 1])) return null;

  const query = prefix.slice(mentionStart + 1);
  if (!query) {
    return { start: mentionStart, end: safeCaret, query: "" };
  }
  if (/[\r\n]$/.test(query) || /\s$/.test(query) || /[.,!?;:]$/.test(query)) return null;
  if (query.includes("@")) return null;

  return {
    start: mentionStart,
    end: safeCaret,
    query,
  };
}

function filterMentionParticipants(participants: ResolvedParticipant[], query: string) {
  const terms = query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);

  if (terms.length === 0) return participants.slice(0, MAX_MENTION_OPTIONS);

  return participants
    .filter((participant) => {
      const haystack = `${participant.label} ${participant.secondaryLabel ?? ""}`.toLowerCase();
      return terms.every((term) => haystack.includes(term));
    })
    .slice(0, MAX_MENTION_OPTIONS);
}

export function ChatView({
  conversation,
  participants,
  mentionParticipants,
  title,
  currentUserRef,
  currentUserName,
  teamId,
  onUpdateGroupParticipants,
  onRenameConversation,
  onDeleteConversation,
}: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isClearing, setIsClearing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [participantsOpen, setParticipantsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [pendingParticipantRefs, setPendingParticipantRefs] = useState<ParticipantRef[]>([]);
  const [renameDraft, setRenameDraft] = useState(conversation.title ?? "");
  const [isRenaming, setIsRenaming] = useState(false);
  const [selectionStart, setSelectionStart] = useState(0);
  const [mentionIndex, setMentionIndex] = useState(0);
  const [dismissedMentionKey, setDismissedMentionKey] = useState<string | null>(null);
  const [activeInfoMessageId, setActiveInfoMessageId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const runtimeState = useConversationRuntime(conversation.id);
  const { typingAgents, streamingReplies, pendingModeratorConfirmation } = runtimeState;

  useEffect(() => subscribeConversationMessages(conversation, setMessages), [conversation]);
  useEffect(() => {
    setIsClearing(false);
    setIsDeleting(false);
    setParticipantsOpen(false);
    setSettingsOpen(false);
    setPendingParticipantRefs([]);
    setIsRenaming(false);
    setSelectionStart(0);
    setMentionIndex(0);
    setDismissedMentionKey(null);
    setActiveInfoMessageId(null);
  }, [conversation.id]);

  useEffect(() => {
    setRenameDraft(conversation.title ?? "");
  }, [conversation.title]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingReplies, typingAgents]);

  const activeMention = useMemo(
    () => (conversation.kind === "channel" ? getActiveMention(draft, selectionStart) : null),
    [conversation.kind, draft, selectionStart],
  );
  const activeMentionKey = activeMention ? `${activeMention.start}:${activeMention.query}` : null;
  const participantIndex = useMemo(
    () => new Map([...participants, ...mentionParticipants].map((participant) => [participant.ref, participant])),
    [mentionParticipants, participants],
  );
  const mentionSuggestions = useMemo(() => {
    if (!activeMention || activeMentionKey === dismissedMentionKey) return [];
    return filterMentionParticipants(mentionParticipants, activeMention.query);
  }, [activeMention, activeMentionKey, dismissedMentionKey, mentionParticipants]);
  const visibleTypingAgents = useMemo(() => {
    const streamingRefs = new Set(streamingReplies.map((reply) => reply.responderRef));
    return typingAgents.filter((agent) => !streamingRefs.has(agent.ref));
  }, [streamingReplies, typingAgents]);
  const groupParticipantOptions = useMemo(() => {
    const map = new Map<ParticipantRef, ResolvedParticipant>();
    for (const participant of [...participants, ...mentionParticipants]) {
      map.set(participant.ref, participant);
    }
    return [...map.values()].sort((a, b) => a.label.localeCompare(b.label));
  }, [mentionParticipants, participants]);
  const existingGroupParticipantRefs = useMemo(
    () => conversation.participantIds,
    [conversation.participantIds],
  );
  const currentGroupParticipantRefs = useMemo(
    () => conversation.participantIds.filter((participantRef) => participantRef !== currentUserRef),
    [conversation.participantIds, currentUserRef],
  );
  const currentGroupParticipants = useMemo(
    () => groupParticipantOptions.filter((participant) => existingGroupParticipantRefs.includes(participant.ref)),
    [existingGroupParticipantRefs, groupParticipantOptions],
  );
  const availableGroupParticipants = useMemo(
    () =>
      groupParticipantOptions.filter(
        (participant) =>
          participant.ref !== currentUserRef && !existingGroupParticipantRefs.includes(participant.ref),
      ),
    [currentUserRef, existingGroupParticipantRefs, groupParticipantOptions],
  );

  useEffect(() => {
    setMentionIndex(0);
  }, [activeMentionKey]);

  useEffect(() => {
    if (messages.length === 0) return;

    const unreadCount = getConversationUnreadCount(conversation, currentUserRef);
    const hasPendingSeenUpdates = messages.some(
      (message) => message.authorId !== currentUserRef && !message.seenBy.includes(currentUserRef),
    );

    if (!hasPendingSeenUpdates && unreadCount === 0) return;
    if (typeof document !== "undefined" && document.visibilityState !== "visible") return;

    const timeoutId = window.setTimeout(() => {
      void markConversationSeen(conversation, currentUserRef, messages).catch((error) => {
        console.error("Failed to mark conversation as seen", error);
      });
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [conversation, currentUserRef, messages]);

  function syncTextareaSelection(element: HTMLTextAreaElement) {
    setSelectionStart(element.selectionStart ?? element.value.length);
  }

  function applyMention(participant: ResolvedParticipant) {
    if (!activeMention || !textareaRef.current) return;

    const nextValue = `${draft.slice(0, activeMention.start)}@${participant.label} ${draft.slice(activeMention.end)}`;
    const nextCaret = activeMention.start + participant.label.length + 2;

    setDraft(nextValue);
    setDismissedMentionKey(null);
    setMentionIndex(0);
    setSelectionStart(nextCaret);

    requestAnimationFrame(() => {
      const textarea = textareaRef.current;
      if (!textarea) return;
      textarea.focus();
      textarea.setSelectionRange(nextCaret, nextCaret);
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 140)}px`;
    });
  }

  async function handleContinueModeratorLoop() {
    try {
      await continueConversationModeratorLoop({
        conversation,
        participants,
        mentionParticipants,
        currentUserRef,
        currentUserName,
        teamId,
        currentMessages: messages,
      });
    } catch (error) {
      console.error("Failed to continue moderated loop", error);
    }
  }

  function handleStopModeratorLoop() {
    dismissConversationModeratorLoop(conversation.id);
  }

  async function handleStopStreaming() {
    await stopConversationRuntime(conversation.id);
  }

  async function send() {
    const text = draft.trim();
    if (!text) return;

    setDraft("");
    setSelectionStart(0);
    setMentionIndex(0);
    setDismissedMentionKey(null);
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    try {
      await sendConversationDraft({
        conversation,
        participants,
        mentionParticipants,
        currentUserRef,
        currentUserName,
        teamId,
        currentMessages: messages,
      }, text);
    } catch (error) {
      console.error("Failed to generate agent reply", error);
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (mentionSuggestions.length > 0) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setMentionIndex((current) => (current + 1) % mentionSuggestions.length);
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setMentionIndex((current) => (current - 1 + mentionSuggestions.length) % mentionSuggestions.length);
        return;
      }
      if (event.key === "Enter" || event.key === "Tab") {
        event.preventDefault();
        applyMention(mentionSuggestions[mentionIndex] ?? mentionSuggestions[0]);
        return;
      }
      if (event.key === "Escape" && activeMentionKey) {
        event.preventDefault();
        setDismissedMentionKey(activeMentionKey);
        return;
      }
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }

  function handleInput(event: React.ChangeEvent<HTMLTextAreaElement>) {
    setDraft(event.target.value);
    setDismissedMentionKey(null);
    const element = event.target;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 140)}px`;
    syncTextareaSelection(element);
  }

  async function handleClearHistory() {
    setIsClearing(true);

    try {
      await stopConversationRuntime(conversation.id);
      await clearConversationHistory(conversation);
      setSettingsOpen(false);
    } catch (error) {
      console.error("Failed to clear conversation history", error);
    } finally {
      setIsClearing(false);
    }
  }

  async function handleRenameConversation() {
    if (conversation.kind === "dm" || !onRenameConversation) return;
    const nextTitle = renameDraft.trim();
    if (!nextTitle || nextTitle === (conversation.title ?? "")) return;

    setIsRenaming(true);
    try {
      await onRenameConversation(conversation.id, nextTitle);
      setSettingsOpen(false);
    } catch (error) {
      console.error("Failed to rename conversation", error);
    } finally {
      setIsRenaming(false);
    }
  }

  async function handleDeleteConversation() {
    if (!onDeleteConversation) return;

    setIsDeleting(true);
    try {
      await stopConversationRuntime(conversation.id);
      await onDeleteConversation(conversation);
      clearConversationRuntime(conversation.id);
      setSettingsOpen(false);
    } catch (error) {
      console.error("Failed to delete conversation", error);
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleUpdateParticipants(nextParticipantRefs: ParticipantRef[]) {
    if (conversation.kind !== "group" || !onUpdateGroupParticipants) return;
    setPendingParticipantRefs(nextParticipantRefs);
    try {
      await onUpdateGroupParticipants(conversation.id, nextParticipantRefs);
    } catch (error) {
      console.error("Failed to update group participants", error);
    } finally {
      setPendingParticipantRefs([]);
    }
  }

  function handleShowMessageInfo(message: ChatMessage) {
    setActiveInfoMessageId((current) => (current === message.id ? null : message.id));
  }

  async function handleEditMessage(message: ChatMessage, content: string) {
    await updateConversationMessage(conversation.id, message.id, content);
  }

  async function handleDeleteMessage(message: ChatMessage) {
    await deleteConversationMessage(conversation, message.id);
    setActiveInfoMessageId((current) => (current === message.id ? null : current));
  }

  const placeholder =
    conversation.kind === "dm"
      ? `Message ${title}`
      : conversation.kind === "channel"
        ? `Message ${conversation.title ?? "channel"} and use @ to mention agents or teammates`
        : `Message ${conversation.title ?? "conversation"}`;
  const isStreaming = streamingReplies.length > 0 || typingAgents.length > 0;

  return (
    <div className="chat-view">
      <div className="chat-view__header">
        <span className="chat-view__title">{conversation.kind === "channel" ? `# ${title}` : title}</span>
        <div className="ml-auto flex items-center gap-2">
          {conversation.kind === "group" ? (
            <Popover open={participantsOpen} onOpenChange={setParticipantsOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-full border-border bg-card/80 px-3"
                >
                  <Users className="size-3.5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="end" className="w-[340px] rounded-2xl border-border/80 p-3 shadow-xl">
                <div className="flex flex-col gap-3">
                  <div className="space-y-1">
                    <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      Participants
                    </p>
                    <p className="text-sm text-foreground">
                      Members already in this group are listed first.
                    </p>
                  </div>
                  <div className="max-h-72 space-y-1 overflow-y-auto pr-1">
                    {currentGroupParticipants.map((participant) => {
                      const isCurrentUser = participant.ref === currentUserRef;
                      const isPending = pendingParticipantRefs.includes(participant.ref);
                      return (
                        <div
                          key={participant.ref}
                          className="group flex items-center gap-3 rounded-xl px-3 py-2 transition-colors hover:bg-muted/70"
                        >
                          <div className="min-w-0 flex-1">
                            <div className="truncate text-sm font-medium text-foreground">{participant.label}</div>
                            <div className="truncate text-xs text-muted-foreground">
                              {isCurrentUser ? "You" : participant.secondaryLabel ?? participant.kind}
                            </div>
                          </div>
                          {!isCurrentUser ? (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-8 rounded-full opacity-0 transition-opacity group-hover:opacity-100"
                              onClick={() =>
                                void handleUpdateParticipants(
                                  currentGroupParticipantRefs.filter((ref) => ref !== participant.ref),
                                )
                              }
                              disabled={isPending}
                              aria-label={`Remove ${participant.label}`}
                            >
                              {isPending ? <Loader2 className="size-3.5 animate-spin" /> : <X className="size-3.5" />}
                            </Button>
                          ) : null}
                        </div>
                      );
                    })}
                    <Separator className="my-2" />
                    {availableGroupParticipants.map((participant) => {
                      const isPending = pendingParticipantRefs.includes(participant.ref);
                      return (
                        <div
                          key={participant.ref}
                          className="group flex items-center gap-3 rounded-xl px-3 py-2 transition-colors hover:bg-muted/70"
                        >
                          <div className="min-w-0 flex-1">
                            <div className="truncate text-sm font-medium text-foreground">{participant.label}</div>
                            <div className="truncate text-xs text-muted-foreground">
                              {participant.secondaryLabel ?? participant.kind}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-8 rounded-full opacity-0 transition-opacity group-hover:opacity-100"
                            onClick={() =>
                              void handleUpdateParticipants([...currentGroupParticipantRefs, participant.ref])
                            }
                            disabled={isPending}
                            aria-label={`Add ${participant.label}`}
                          >
                            {isPending ? <Loader2 className="size-3.5 animate-spin" /> : <Plus className="size-3.5" />}
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          ) : null}
          <Popover open={settingsOpen} onOpenChange={setSettingsOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-9 w-9 rounded-full border-border bg-card/80 p-0"
                aria-label="Chat settings"
                title="Chat settings"
              >
                <Settings2 className="size-3.5" />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-[340px] rounded-2xl border-border/80 p-3 shadow-xl">
              <div className="flex flex-col gap-4">
                <div className="space-y-1">
                  <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    Chat Settings
                  </p>
                  <p className="text-sm text-foreground">
                    Manage this conversation without leaving the thread.
                  </p>
                </div>
                {conversation.kind !== "dm" ? (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">Rename conversation</p>
                    <div className="flex items-center gap-2">
                      <Input
                        value={renameDraft}
                        onChange={(event) => setRenameDraft(event.target.value)}
                        placeholder="Conversation name"
                        className="h-9 rounded-xl"
                      />
                      <Button
                        size="sm"
                        className="rounded-xl"
                        onClick={() => void handleRenameConversation()}
                        disabled={
                          isRenaming ||
                          !renameDraft.trim() ||
                          renameDraft.trim() === (conversation.title ?? "")
                        }
                      >
                        {isRenaming ? <Loader2 className="size-4 animate-spin" /> : "Save"}
                      </Button>
                    </div>
                  </div>
                ) : null}
                <Separator />
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">Danger zone</p>
                  <Button
                    variant="outline"
                    className="w-full justify-start rounded-xl"
                    onClick={() => void handleClearHistory()}
                    disabled={isClearing}
                  >
                    {isClearing ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
                    Clear chat history
                  </Button>
                  <Button
                    variant="destructive"
                    className="w-full justify-start rounded-xl"
                    onClick={() => void handleDeleteConversation()}
                    disabled={isDeleting}
                  >
                    {isDeleting ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
                    Delete conversation
                  </Button>
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <div className="chat-view__messages relative">
        {messages.length === 0 ? (
          <div className="chat-view__empty">No chat history yet.</div>
        ) : (
          messages.map((message, index) => {
            const previous = messages[index - 1];
            const showHeader =
              !previous ||
              previous.authorId !== message.authorId ||
              message.createdAt - previous.createdAt > 5 * 60 * 1000;
            const author = participantIndex.get(message.authorId as ParticipantRef);

            return (
              <Message
                key={message.id}
                message={message}
                showHeader={showHeader}
                currentUserId={currentUserRef}
                authorJobTitle={author?.kind === "agent" ? author.secondaryLabel : null}
                onShowInfo={handleShowMessageInfo}
                onEditMessage={handleEditMessage}
                onDeleteMessage={handleDeleteMessage}
                activeInfoMessageId={activeInfoMessageId}
              />
            );
          })
        )}
        {streamingReplies.map((reply) => (
          <StreamingMessage
            key={`stream-${reply.responderRef}`}
            authorId={reply.responderRef}
            authorName={reply.authorName}
            authorJobTitle={reply.authorJobTitle}
            statusLabel={reply.statusLabel}
            thoughtProcess={reply.thoughtProcess}
            commentary={reply.commentary}
            finalText={reply.finalText}
            toolEvents={reply.toolEvents}
          />
        ))}
        <TypingMessage
          authors={visibleTypingAgents.map((agent) => ({
            id: agent.ref,
            name: agent.label,
          }))}
        />
        <div ref={bottomRef} />
      </div>

      <div className="chat-view__input-bar">
        <div className="chat-view__composer">
          {pendingModeratorConfirmation ? (
            <div className="chat-view__loop-guard" role="status" aria-live="polite">
              <div className="chat-view__loop-guard-copy">
                <span className="chat-view__loop-guard-title">Continue agent conversation?</span>
                <span className="chat-view__loop-guard-text">
                  {pendingModeratorConfirmation.consecutiveAgentMessages} agent messages have been sent without a user
                  reply. Continue and let the moderator choose the next responder, or stop here.
                </span>
              </div>
              <div className="chat-view__loop-guard-actions">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="rounded-xl"
                  onClick={() => void handleStopModeratorLoop()}
                >
                  Stop
                </Button>
                <Button
                  type="button"
                  size="sm"
                  className="rounded-xl"
                  onClick={() => void handleContinueModeratorLoop()}
                >
                  Continue
                </Button>
              </div>
            </div>
          ) : null}
          {mentionSuggestions.length > 0 ? (
            <div className="chat-view__mention-menu">
              {mentionSuggestions.map((participant, index) => (
                <button
                  key={participant.ref}
                  type="button"
                  className={`chat-view__mention-option${index === mentionIndex ? " active" : ""}`}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => applyMention(participant)}
                >
                  <span className="chat-view__mention-avatar">
                    {participant.kind === "agent" ? "A" : "U"}
                  </span>
                  <span className="chat-view__mention-copy">
                    <span className="chat-view__mention-label">{participant.label}</span>
                    <span className="chat-view__mention-meta">
                      {participant.secondaryLabel ?? (participant.kind === "agent" ? "Agent" : "User")}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          ) : null}
          <Textarea
            ref={textareaRef}
            className="chat-view__textarea min-h-0 rounded-2xl border-input bg-background/85 px-4 py-3 shadow-none"
            placeholder={placeholder}
            rows={1}
            value={draft}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            onClick={(event) => syncTextareaSelection(event.currentTarget)}
            onKeyUp={(event) => syncTextareaSelection(event.currentTarget)}
            onSelect={(event) => syncTextareaSelection(event.currentTarget)}
          />
        </div>
        <Button
          className="chat-view__send-btn h-11 w-11 rounded-2xl p-0"
          onClick={() => void (isStreaming ? handleStopStreaming() : send())}
          disabled={!isStreaming && !draft.trim()}
          aria-label={isStreaming ? "Stop response" : "Send"}
          title={isStreaming ? "Stop response" : "Send"}
        >
          {isStreaming ? (
            <Square className="size-4 fill-current" />
          ) : (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M14 8L2 2l2.5 6L2 14l12-6z" fill="currentColor" />
            </svg>
          )}
        </Button>
      </div>
    </div>
  );
}
