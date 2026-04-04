"use client";

import { useEffect, useState } from "react";
import {
  listConversationMessages,
  moderateChannelResponders,
  sendConversationMessage,
  setConversationTypingParticipant,
  stopConversationReply,
  streamConversationReply,
  type ChatMessage,
  type Conversation,
  type ParticipantRef,
  type ResolvedParticipant,
  type StreamedToolEvent,
} from "./chat-service";

const MAX_AUTOMATED_AGENT_RESPONSES = 20;

export type ActiveStreamingReply = {
  responderRef: ParticipantRef;
  authorName: string;
  authorJobTitle: string | null;
  statusLabel: string;
  thoughtProcess: string[];
  commentary: string;
  finalText: string;
  runId: string;
  toolEvents: StreamedToolEvent[];
};

export type PendingModeratorConfirmation = {
  history: ChatMessage[];
  consecutiveAgentMessages: number;
};

export type ConversationRuntimeState = {
  typingAgents: ResolvedParticipant[];
  streamingReplies: ActiveStreamingReply[];
  pendingModeratorConfirmation: PendingModeratorConfirmation | null;
  agentLoopCheckpoint: number;
};

type ConversationRuntimeInput = {
  conversation: Conversation;
  participants: ResolvedParticipant[];
  mentionParticipants: ResolvedParticipant[];
  currentUserRef: ParticipantRef;
  currentUserName: string;
  teamId: string;
  currentMessages: ChatMessage[];
};

type RuntimeContextSnapshot = ConversationRuntimeInput & {
  participantIndex: Map<ParticipantRef, ResolvedParticipant>;
  routingAgentCandidates: ResolvedParticipant[];
  conversationParticipantsPayload: Array<{
    ref: ParticipantRef;
    name: string;
    job: string | null;
    kind: "user" | "agent";
  }>;
};

type StreamControl = {
  controller: AbortController;
  runId: string;
  stopRequested: boolean;
};

type ConversationRuntimeController = {
  state: ConversationRuntimeState;
  listeners: Set<(state: ConversationRuntimeState) => void>;
  activeStreams: Map<ParticipantRef, StreamControl>;
  stopRequested: boolean;
};

const controllers = new Map<string, ConversationRuntimeController>();

const EMPTY_RUNTIME_STATE: ConversationRuntimeState = {
  typingAgents: [],
  streamingReplies: [],
  pendingModeratorConfirmation: null,
  agentLoopCheckpoint: 0,
};

function formatTraceNode(node?: string) {
  if (!node) return "";

  return node
    .split("/")
    .filter(Boolean)
    .map((segment) =>
      segment
        .split("_")
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" "),
    )
    .join(" > ");
}

function formatTraceStep(node: string | undefined, text: string) {
  const cleanText = text.trim();
  const label = formatTraceNode(node);
  if (!cleanText) return "";
  return label ? `${label}: ${cleanText}` : cleanText;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function extractMentionedAgentRefs(
  content: string,
  participants: ResolvedParticipant[],
) {
  const agentParticipants = participants
    .filter((participant) => participant.kind === "agent")
    .sort((left, right) => right.label.length - left.label.length);

  const matchedAgentRefs: ParticipantRef[] = [];
  const seen = new Set<ParticipantRef>();

  for (const participant of agentParticipants) {
    const label = participant.label.trim();
    if (!label) continue;

    const pattern = new RegExp(`(^|\\s)@${escapeRegExp(label)}(?=$|\\s|[.,!?;:])`, "i");
    if (!pattern.test(content)) continue;

    if (!seen.has(participant.ref)) {
      seen.add(participant.ref);
      matchedAgentRefs.push(participant.ref);
    }
  }

  return matchedAgentRefs;
}

function activeConversationParticipants(
  participantRefs: ParticipantRef[],
  participantIndex: Map<ParticipantRef, ResolvedParticipant>,
) {
  return participantRefs
    .map((participantRef) => participantIndex.get(participantRef))
    .filter((participant): participant is ResolvedParticipant => Boolean(participant));
}

function countConsecutiveAgentMessages(history: ChatMessage[]) {
  let count = 0;

  for (let index = history.length - 1; index >= 0; index -= 1) {
    if (!history[index].authorId.startsWith("agent:")) {
      break;
    }
    count += 1;
  }

  return count;
}

function getController(conversationId: string) {
  let controller = controllers.get(conversationId);
  if (!controller) {
    controller = {
      state: { ...EMPTY_RUNTIME_STATE },
      listeners: new Set(),
      activeStreams: new Map(),
      stopRequested: false,
    };
    controllers.set(conversationId, controller);
  }
  return controller;
}

function emit(conversationId: string) {
  const controller = getController(conversationId);
  const nextState = controller.state;
  for (const listener of controller.listeners) {
    listener(nextState);
  }
}

function setControllerState(
  conversationId: string,
  updater: (current: ConversationRuntimeState) => ConversationRuntimeState,
) {
  const controller = getController(conversationId);
  controller.state = updater(controller.state);
  emit(conversationId);
}

function buildRuntimeContext(input: ConversationRuntimeInput): RuntimeContextSnapshot {
  const participantIndex = new Map(
    [...input.participants, ...input.mentionParticipants].map((participant) => [participant.ref, participant]),
  );
  const routingAgentCandidates =
    (input.conversation.kind === "channel" ? input.mentionParticipants : input.participants).filter(
      (participant): participant is ResolvedParticipant =>
        participant.kind === "agent" && Boolean(participant.secondaryLabel),
    );

  return {
    ...input,
    participantIndex,
    routingAgentCandidates,
    conversationParticipantsPayload: activeConversationParticipants(
      input.conversation.participantIds,
      participantIndex,
    ).map((participant) => ({
      ref: participant.ref,
      name: participant.label,
      job: participant.kind === "agent" ? participant.secondaryLabel : null,
      kind: participant.kind,
    })),
  };
}

function upsertStreamingReply(
  conversationId: string,
  responder: ResolvedParticipant,
  updater: (current: ActiveStreamingReply) => ActiveStreamingReply,
) {
  setControllerState(conversationId, (current) => {
    const index = current.streamingReplies.findIndex((item) => item.responderRef === responder.ref);
    const base: ActiveStreamingReply =
      index >= 0
        ? current.streamingReplies[index]
        : {
            responderRef: responder.ref,
            authorName: responder.label,
            authorJobTitle: responder.secondaryLabel,
            statusLabel: "Processing User Request",
            thoughtProcess: ["Processing User Request"],
            commentary: "",
            finalText: "",
            runId: "",
            toolEvents: [],
          };
    const next = updater(base);
    if (index < 0) {
      return {
        ...current,
        streamingReplies: [...current.streamingReplies, next],
      };
    }

    const copy = [...current.streamingReplies];
    copy[index] = next;
    return {
      ...current,
      streamingReplies: copy,
    };
  });
}

function removeStreamingReply(conversationId: string, responderRef: ParticipantRef) {
  setControllerState(conversationId, (current) => ({
    ...current,
    streamingReplies: current.streamingReplies.filter((item) => item.responderRef !== responderRef),
  }));
}

function unregisterActiveStream(conversationId: string, responderRef: ParticipantRef) {
  getController(conversationId).activeStreams.delete(responderRef);
}

function getStreamRequestMessages(
  history: ChatMessage[],
  responderRef: ParticipantRef,
  participantIndex: Map<ParticipantRef, ResolvedParticipant>,
) {
  return history.map((message) => ({
    role: message.authorId === responderRef ? "assistant" as const : "user" as const,
    authorId: message.authorId as ParticipantRef,
    author: message.authorName,
    authorJob:
      participantIndex.get(message.authorId as ParticipantRef)?.kind === "agent"
        ? participantIndex.get(message.authorId as ParticipantRef)?.secondaryLabel ?? null
        : null,
    authorKind: participantIndex.get(message.authorId as ParticipantRef)?.kind ?? "user",
    content: message.content,
  }));
}

function getModeratorMessages(
  history: ChatMessage[],
  participantIndex: Map<ParticipantRef, ResolvedParticipant>,
) {
  return history.map((message) => ({
    role: message.authorId.startsWith("agent:") ? "assistant" as const : "user" as const,
    authorId: message.authorId as ParticipantRef,
    author: message.authorName,
    authorJob:
      participantIndex.get(message.authorId as ParticipantRef)?.kind === "agent"
        ? participantIndex.get(message.authorId as ParticipantRef)?.secondaryLabel ?? null
        : null,
    authorKind: participantIndex.get(message.authorId as ParticipantRef)?.kind ?? "user",
    content: message.content,
  }));
}

async function syncTypingParticipant(
  conversationId: string,
  participantRef: ParticipantRef,
  isTyping: boolean,
) {
  try {
    await setConversationTypingParticipant(conversationId, participantRef, isTyping);
  } catch (error) {
    console.error("Failed to sync typing state", error);
  }
}

function mergeTypingAgents(conversationId: string, additions: ResolvedParticipant[]) {
  const nextRefs = additions.map((agent) => agent.ref);

  setControllerState(conversationId, (current) => {
    const seen = new Set(current.typingAgents.map((item) => item.ref));
    const merged = [...current.typingAgents];
    for (const agent of additions) {
      if (!seen.has(agent.ref)) {
        seen.add(agent.ref);
        merged.push(agent);
      }
    }
    return {
      ...current,
      typingAgents: merged,
    };
  });

  for (const responderRef of nextRefs) {
    void syncTypingParticipant(conversationId, responderRef, true);
  }
}

function removeTypingAgent(conversationId: string, responderRef: ParticipantRef) {
  setControllerState(conversationId, (current) => ({
    ...current,
    typingAgents: current.typingAgents.filter((item) => item.ref !== responderRef),
  }));
  void syncTypingParticipant(conversationId, responderRef, false);
}

async function decideModeratedResponders(
  context: RuntimeContextSnapshot,
  history: ChatMessage[],
) {
  if (context.routingAgentCandidates.length === 0) return [];

  const latestMessage = history[history.length - 1] ?? null;
  const latestMessagerAgentRef =
    latestMessage && latestMessage.authorId.startsWith("agent:")
      ? (latestMessage.authorId as ParticipantRef)
      : null;
  const moderatorCandidates = context.routingAgentCandidates.filter(
    (participant) => participant.ref !== latestMessagerAgentRef,
  );

  if (moderatorCandidates.length === 0) {
    return [];
  }

  const selectedAgentRefs = await moderateChannelResponders({
    conversationKind: context.conversation.kind,
    conversationTitle: context.conversation.title,
    conversationParticipants: context.conversationParticipantsPayload,
    teamId: context.teamId,
    messages: getModeratorMessages(history, context.participantIndex),
    availableAgents: moderatorCandidates.map((participant) => ({
      ref: participant.ref,
      name: participant.label,
      job: participant.secondaryLabel ?? "",
      description: participant.description,
      personality: participant.personality,
    })),
  });

  return selectedAgentRefs
    .map((ref) => context.participantIndex.get(ref as ParticipantRef))
    .filter(
      (participant): participant is ResolvedParticipant =>
        Boolean(participant && participant.kind === "agent" && participant.secondaryLabel),
    );
}

function resolveMentionedResponders(
  content: string,
  routingAgentCandidates: ResolvedParticipant[],
  participantIndex: Map<ParticipantRef, ResolvedParticipant>,
) {
  return extractMentionedAgentRefs(content, routingAgentCandidates)
    .map((ref) => participantIndex.get(ref))
    .filter(
      (participant): participant is ResolvedParticipant =>
        Boolean(participant && participant.kind === "agent" && participant.secondaryLabel),
    );
}

async function requestAgentReply(
  context: RuntimeContextSnapshot,
  responder: ResolvedParticipant,
  history: ChatMessage[],
  options?: {
    handoffRequestedByName?: string;
    handoffRequestedByJob?: string | null;
    handoffReason?: string;
    handoffPrompt?: string;
    resumeRunId?: string;
  },
) {
  const { conversation } = context;
  const runtime = getController(conversation.id);

  upsertStreamingReply(conversation.id, responder, (current) => ({
    ...current,
    statusLabel: "Processing User Request",
    thoughtProcess: ["Processing User Request"],
    commentary: "",
    finalText: "",
    toolEvents: [],
  }));

  const abortController = new AbortController();
  let latestRunId = options?.resumeRunId ?? "";
  let partialFinalText = "";
  const thoughtProcess = ["Processing User Request"];
  runtime.activeStreams.set(responder.ref, {
    controller: abortController,
    runId: latestRunId,
    stopRequested: false,
  });

  try {
    const appendThoughtStage = (stage: string) => {
      const value = stage.trim();
      if (!value || thoughtProcess[thoughtProcess.length - 1] === value) return;
      thoughtProcess.push(value);
    };

    const reply = await streamConversationReply(
      {
        projectId: conversation.projectId,
        conversationId: conversation.id,
        conversationKind: conversation.kind,
        conversationTitle: conversation.title,
        conversationParticipants: context.conversationParticipantsPayload,
        responderName: responder.label,
        responderJob: responder.secondaryLabel,
        responderDescription: responder.description,
        responderPersonality: responder.personality,
        currentResponderRef: responder.ref,
        resumeRunId: options?.resumeRunId ?? "",
        teamId: responder.teamId ?? context.teamId,
        availableAgents:
          conversation.kind === "dm"
            ? undefined
            : context.routingAgentCandidates.map((participant) => ({
                ref: participant.ref,
                name: participant.label,
                job: participant.secondaryLabel ?? "",
                description: participant.description,
                personality: participant.personality,
              })),
        handoffDepth: 0,
        handoffRequestedByName: options?.handoffRequestedByName ?? "",
        handoffRequestedByJob: options?.handoffRequestedByJob ?? "",
        handoffReason: options?.handoffReason ?? "",
        handoffPrompt: options?.handoffPrompt ?? "",
        messages: getStreamRequestMessages(history, responder.ref, context.participantIndex),
      },
      {
        onRunStarted: ({ runId }) => {
          latestRunId = runId;
          const activeStream = getController(conversation.id).activeStreams.get(responder.ref);
          if (activeStream) {
            activeStream.runId = runId;
          }
          upsertStreamingReply(conversation.id, responder, (current) => ({ ...current, runId }));
        },
        onCommentaryDelta: ({ textDelta }) => {
          upsertStreamingReply(conversation.id, responder, (current) => ({
            ...current,
            commentary: `${current.commentary}${textDelta}`,
          }));
        },
        onCommentaryCompleted: ({ node, text, statusText }) => {
          const formattedStep = formatTraceStep(node, text);
          appendThoughtStage(formattedStep);
          upsertStreamingReply(conversation.id, responder, (current) => ({
            ...current,
            statusLabel: statusText || text || current.statusLabel,
            thoughtProcess:
              formattedStep && current.thoughtProcess[current.thoughtProcess.length - 1] !== formattedStep
                ? [...current.thoughtProcess, formattedStep]
                : current.thoughtProcess,
          }));
        },
        onToolEvent: (toolEvent) => {
          upsertStreamingReply(conversation.id, responder, (current) => {
            const index = current.toolEvents.findIndex((item) => item.callId === toolEvent.callId);
            const nextToolEvents = [...current.toolEvents];
            if (index < 0) {
              nextToolEvents.push(toolEvent);
            } else {
              nextToolEvents[index] = toolEvent;
            }
            return {
              ...current,
              toolEvents: nextToolEvents,
            };
          });
        },
        onClarificationRequested: ({ content, runId }) => {
          partialFinalText = content;
          upsertStreamingReply(conversation.id, responder, (current) => ({
            ...current,
            finalText: content,
            runId,
          }));
        },
        onFinalDelta: ({ textDelta }) => {
          partialFinalText = `${partialFinalText}${textDelta}`;
          upsertStreamingReply(conversation.id, responder, (current) => ({
            ...current,
            finalText: `${current.finalText}${textDelta}`,
          }));
        },
      },
      {
        signal: abortController.signal,
      },
    );

    await sendConversationMessage(
      conversation,
      responder.ref,
      responder.label,
      reply.content,
      reply.imageUrl,
      reply.videoUrl,
      {
        phase: reply.phase,
        runId: reply.runId,
        thoughtProcess,
      },
    );
    removeStreamingReply(conversation.id, responder.ref);

    const replyMessage: ChatMessage = {
      id: `pending-agent-message-${responder.ref}-${Date.now()}`,
      authorId: responder.ref,
      authorName: responder.label,
      content: reply.content,
      imageUrl: reply.imageUrl,
      videoUrl: reply.videoUrl,
      thoughtProcess,
      phase: reply.phase,
      runId: reply.runId,
      createdAt: Date.now(),
      seenBy: [responder.ref],
    };

    return {
      history: [...history, replyMessage],
      replyMessage,
      waitingForUser: reply.waitingForUser,
    };
  } catch (error) {
    const activeStream = getController(conversation.id).activeStreams.get(responder.ref);
    const wasStopped = runtime.stopRequested || Boolean(activeStream?.stopRequested);
    const isAbort = error instanceof DOMException && error.name === "AbortError";

    if (wasStopped && (isAbort || abortController.signal.aborted)) {
      const partialContent = partialFinalText.trim();
      removeStreamingReply(conversation.id, responder.ref);
      unregisterActiveStream(conversation.id, responder.ref);

      if (!partialContent) {
        return {
          history,
          replyMessage: null,
          waitingForUser: false,
        };
      }

      await sendConversationMessage(
        conversation,
        responder.ref,
        responder.label,
        partialContent,
        null,
        null,
        {
          phase: "final_answer",
          runId: latestRunId || null,
          thoughtProcess,
        },
      );

      const partialMessage: ChatMessage = {
        id: `stopped-agent-message-${responder.ref}-${Date.now()}`,
        authorId: responder.ref,
        authorName: responder.label,
        content: partialContent,
        thoughtProcess,
        phase: "final_answer",
        runId: latestRunId || null,
        createdAt: Date.now(),
        seenBy: [responder.ref],
      };

      return {
        history: [...history, partialMessage],
        replyMessage: partialMessage,
        waitingForUser: false,
      };
    }

    removeStreamingReply(conversation.id, responder.ref);
    throw error;
  } finally {
    unregisterActiveStream(conversation.id, responder.ref);
  }
}

async function runAutoResponseQueue(
  context: RuntimeContextSnapshot,
  history: ChatMessage[],
  initialResponders: ResolvedParticipant[],
) {
  let currentHistory = history;
  const queue = [...initialResponders];
  const queuedRefs = new Set(queue.map((agent) => agent.ref));
  let shouldRunModeratorAfterQueue = false;
  let responseCount = 0;

  const enqueueResponders = (responders: ResolvedParticipant[]) => {
    const nextAgents: ResolvedParticipant[] = [];
    for (const agent of responders) {
      if (queuedRefs.has(agent.ref)) continue;
      queuedRefs.add(agent.ref);
      queue.push(agent);
      nextAgents.push(agent);
    }
    if (nextAgents.length > 0) {
      mergeTypingAgents(context.conversation.id, nextAgents);
    }
  };

  mergeTypingAgents(context.conversation.id, initialResponders);

  while (!getController(context.conversation.id).stopRequested && responseCount < MAX_AUTOMATED_AGENT_RESPONSES) {
    while (
      queue.length > 0 &&
      !getController(context.conversation.id).stopRequested &&
      responseCount < MAX_AUTOMATED_AGENT_RESPONSES
    ) {
      const responder = queue.shift();
      if (!responder) {
        continue;
      }
      queuedRefs.delete(responder.ref);
      responseCount += 1;

      try {
        const result = await requestAgentReply(context, responder, currentHistory);
        currentHistory = result.history;

        if (getController(context.conversation.id).stopRequested) {
          continue;
        }

        if (
          result.waitingForUser ||
          !result.replyMessage ||
          (context.conversation.kind !== "channel" && context.conversation.kind !== "group")
        ) {
          continue;
        }

        const mentionedResponders = resolveMentionedResponders(
          result.replyMessage.content,
          context.routingAgentCandidates,
          context.participantIndex,
        ).filter((agent) => agent.ref !== responder.ref);

        if (mentionedResponders.length > 0) {
          enqueueResponders(mentionedResponders);
        } else {
          shouldRunModeratorAfterQueue = true;
        }
      } finally {
        removeTypingAgent(context.conversation.id, responder.ref);
      }
    }

    if (
      getController(context.conversation.id).stopRequested ||
      responseCount >= MAX_AUTOMATED_AGENT_RESPONSES ||
      !shouldRunModeratorAfterQueue ||
      (context.conversation.kind !== "channel" && context.conversation.kind !== "group")
    ) {
      break;
    }

    const consecutiveAgentMessages = countConsecutiveAgentMessages(currentHistory);
    const agentLoopCheckpoint = getController(context.conversation.id).state.agentLoopCheckpoint;
    if (consecutiveAgentMessages - agentLoopCheckpoint >= 7) {
      setControllerState(context.conversation.id, (current) => ({
        ...current,
        pendingModeratorConfirmation: {
          history: currentHistory,
          consecutiveAgentMessages,
        },
      }));
      break;
    }

    shouldRunModeratorAfterQueue = false;
    const moderatedResponders = await decideModeratedResponders(context, currentHistory);
    if (moderatedResponders.length === 0) {
      break;
    }
    enqueueResponders(moderatedResponders);
  }

  return currentHistory;
}

export function subscribeConversationRuntime(
  conversationId: string,
  listener: (state: ConversationRuntimeState) => void,
) {
  const controller = getController(conversationId);
  controller.listeners.add(listener);
  listener(controller.state);

  return () => {
    const current = controllers.get(conversationId);
    if (!current) return;
    current.listeners.delete(listener);
  };
}

export function useConversationRuntime(conversationId: string) {
  const [state, setState] = useState<ConversationRuntimeState>(() => getController(conversationId).state);

  useEffect(() => subscribeConversationRuntime(conversationId, setState), [conversationId]);

  return state;
}

export async function sendConversationDraft(input: ConversationRuntimeInput, draft: string) {
  const context = buildRuntimeContext(input);
  const controller = getController(context.conversation.id);
  const text = draft.trim();
  if (!text) return;

  controller.stopRequested = false;
  setControllerState(context.conversation.id, (current) => ({
    ...current,
    pendingModeratorConfirmation: null,
    agentLoopCheckpoint: 0,
  }));

  const mentionedAgentRefs = (context.conversation.kind === "channel" || context.conversation.kind === "group")
    ? extractMentionedAgentRefs(text, context.routingAgentCandidates)
    : [];

  const pendingUserMessage: ChatMessage = {
    id: "pending-user-message",
    authorId: context.currentUserRef,
    authorName: context.currentUserName,
    content: text,
    createdAt: Date.now(),
    seenBy: [context.currentUserRef],
  };

  await sendConversationMessage(
    context.conversation,
    context.currentUserRef,
    context.currentUserName,
    text,
  );

  const history = await listConversationMessages(context.conversation)
    .then((items) => (items.length > 0 ? items : [...context.currentMessages, pendingUserMessage]))
    .catch(() => [...context.currentMessages, pendingUserMessage]);

  const latestClarification = [...history]
    .reverse()
    .find(
      (message) =>
        message.phase === "clarification" &&
        Boolean(message.runId) &&
        message.authorId.startsWith("agent:"),
    );

  if (latestClarification?.runId) {
    const resumedResponder = context.participantIndex.get(latestClarification.authorId as ParticipantRef);
    if (resumedResponder && resumedResponder.kind === "agent" && resumedResponder.secondaryLabel) {
      const resumedResult = await requestAgentReply(context, resumedResponder, history, {
        resumeRunId: latestClarification.runId,
      });

      if (controller.stopRequested) {
        return;
      }

      if (
        resumedResult.waitingForUser ||
        !resumedResult.replyMessage ||
        (context.conversation.kind !== "channel" && context.conversation.kind !== "group")
      ) {
        return;
      }

      const mentionedResponders = resolveMentionedResponders(
        resumedResult.replyMessage.content,
        context.routingAgentCandidates,
        context.participantIndex,
      ).filter((agent) => agent.ref !== resumedResponder.ref);

      if (mentionedResponders.length > 0) {
        await runAutoResponseQueue(context, resumedResult.history, mentionedResponders);
        return;
      }

      const moderatedResponders = await decideModeratedResponders(context, resumedResult.history);
      if (moderatedResponders.length > 0) {
        await runAutoResponseQueue(context, resumedResult.history, moderatedResponders);
      }
      return;
    }
  }

  if (context.conversation.kind === "channel" || context.conversation.kind === "group") {
    const explicitlyMentionedAgents = mentionedAgentRefs
      .map((ref) => context.participantIndex.get(ref))
      .filter(
        (participant): participant is ResolvedParticipant =>
          Boolean(participant && participant.kind === "agent" && participant.secondaryLabel),
      );

    if (explicitlyMentionedAgents.length > 0) {
      await runAutoResponseQueue(context, history, explicitlyMentionedAgents);
      return;
    }

    const selectedAgents = await decideModeratedResponders(context, history);
    if (selectedAgents.length === 0) return;

    await runAutoResponseQueue(context, history, selectedAgents);
    return;
  }

  const responder =
    context.participants.find(
      (participant) => participant.kind === "agent" && participant.ref !== context.currentUserRef,
    ) ?? null;

  if (!responder) return;

  mergeTypingAgents(context.conversation.id, [responder]);
  try {
    await requestAgentReply(context, responder, history);
  } finally {
    removeTypingAgent(context.conversation.id, responder.ref);
  }
}

export async function continueConversationModeratorLoop(input: ConversationRuntimeInput) {
  const context = buildRuntimeContext(input);
  const controller = getController(context.conversation.id);
  const snapshot = controller.state.pendingModeratorConfirmation;
  if (!snapshot) return;

  setControllerState(context.conversation.id, (current) => ({
    ...current,
    agentLoopCheckpoint: snapshot.consecutiveAgentMessages,
    pendingModeratorConfirmation: null,
  }));

  const moderatedResponders = await decideModeratedResponders(context, snapshot.history);
  if (moderatedResponders.length === 0) {
    return;
  }

  await runAutoResponseQueue(context, snapshot.history, moderatedResponders);
}

export function dismissConversationModeratorLoop(conversationId: string) {
  setControllerState(conversationId, (current) => ({
    ...current,
    pendingModeratorConfirmation: null,
  }));
}

export async function stopConversationRuntime(conversationId: string) {
  const controller = getController(conversationId);
  controller.stopRequested = true;

  const activeStreams = [...controller.activeStreams.entries()];

  await Promise.allSettled(
    activeStreams.map(async ([participantRef, stream]) => {
      stream.stopRequested = true;
      if (stream.runId) {
        try {
          await stopConversationReply({
            conversationId,
            runId: stream.runId,
          });
        } catch (error) {
          console.error("Failed to stop backend stream", error);
        }
      }
      stream.controller.abort();
      await syncTypingParticipant(conversationId, participantRef, false);
    }),
  );
}

export function clearConversationRuntime(conversationId: string) {
  controllers.delete(conversationId);
}
