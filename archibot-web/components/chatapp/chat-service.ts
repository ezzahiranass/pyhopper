import {
  addDoc,
  arrayRemove,
  arrayUnion,
  collection,
  deleteDoc,
  doc,
  documentId,
  getDoc,
  getDocs,
  increment,
  limit,
  limitToLast,
  onSnapshot,
  orderBy,
  query,
  serverTimestamp,
  setDoc,
  Timestamp,
  updateDoc,
  where,
  writeBatch,
  type DocumentData,
  type QueryDocumentSnapshot,
} from "firebase/firestore";
import { db } from "@/lib/firebase";




export type ConversationKind = "channel" | "group" | "dm";
export type ParticipantKind = "user" | "agent";
export type ParticipantRef = `user:${string}` | `agent:${string}`;

export type Conversation = {
  id: string;
  projectId: string;
  kind: ConversationKind;
  title: string | null;
  participantIds: ParticipantRef[];
  createdAt: number;
  updatedAt: number;
  lastMessageAt: number;
  createdBy: ParticipantRef | null;
  dmKey: string | null;
  typingParticipantRefs: ParticipantRef[];
  unreadCountByParticipant: Record<string, number>;
  lastSeenAtByParticipant: Record<string, number>;
};

export type ChatMessage = {
  id: string;
  authorId: string;
  authorName: string;
  content: string;
  imageUrl?: string | null;
  videoUrl?: string | null;
  thoughtProcess?: string[] | null;
  phase?: "final_answer" | "clarification" | null;
  runId?: string | null;
  createdAt: number;
  seenBy: ParticipantRef[];
};

type ChatCompletionRequest = {
  projectId: string;
  conversationId: string;
  conversationKind: ConversationKind;
  conversationTitle: string | null;
  conversationParticipants?: Array<{
    ref: ParticipantRef;
    name: string;
    job: string | null;
    kind: ParticipantKind;
  }>;
  responderName: string;
  responderJob: string | null;
  responderDescription: string | null;
  responderPersonality: string | null;
  currentResponderRef?: ParticipantRef;
  resumeRunId?: string;
  teamId: string;
  availableAgents?: Array<{
    ref: ParticipantRef;
    name: string;
    job: string;
    description: string | null;
    personality: string | null;
  }>;
  handoffDepth?: number;
  handoffRequestedByName?: string;
  handoffRequestedByJob?: string | null;
  handoffReason?: string;
  handoffPrompt?: string;
  messages: Array<{
    role: "user" | "assistant";
    authorId?: ParticipantRef;
    author: string;
    authorJob?: string | null;
    authorKind?: ParticipantKind;
    content: string;
  }>;
};

export type StreamedToolEvent = {
  node?: string;
  toolName: string;
  callId: string;
  args?: unknown;
  output?: unknown;
  error?: string;
  status: "started" | "completed" | "failed";
};

export type StreamedReply = {
  content: string;
  imageUrl: string | null;
  videoUrl: string | null;
  requestedAgentRefs: string[];
  handoffReason: string;
  handoffPrompt: string;
  phase: "final_answer" | "clarification";
  runId: string;
  waitingForUser: boolean;
};

type StreamConversationReplyHandlers = {
  onRunStarted?: (payload: { runId: string; status: string }) => void;
  onNodeEntered?: (payload: { node: string }) => void;
  onCommentaryDelta?: (payload: { node: string; textDelta: string }) => void;
  onCommentaryCompleted?: (payload: { node: string; text: string; statusText?: string }) => void;
  onToolEvent?: (payload: StreamedToolEvent) => void;
  onClarificationRequested?: (payload: { content: string; phase: "clarification"; runId: string }) => void;
  onFinalDelta?: (payload: { textDelta: string }) => void;
  onFinalCompleted?: (payload: { content: string; phase: "final_answer" }) => void;
};

type StopConversationReplyRequest = {
  conversationId: string;
  runId: string;
};

type ModeratorRequest = {
  conversationKind: ConversationKind;
  conversationTitle: string | null;
  conversationParticipants?: Array<{
    ref: ParticipantRef;
    name: string;
    job: string | null;
    kind: ParticipantKind;
  }>;
  teamId: string;
  messages: Array<{
    role: "user" | "assistant";
    authorId?: ParticipantRef;
    author: string;
    authorJob?: string | null;
    authorKind?: ParticipantKind;
    content: string;
  }>;
  availableAgents: Array<{
    ref: ParticipantRef;
    name: string;
    job: string;
    description: string | null;
    personality: string | null;
  }>;
};

export type ResolvedParticipant = {
  ref: ParticipantRef;
  sourceId: string;
  kind: ParticipantKind;
  label: string;
  secondaryLabel: string | null;
  description: string | null;
  personality: string | null;
  teamId: string | null;
};

export type Member = {
  uid: string;
  displayName: string | null;
  email: string | null;
};

export type AgentMember = {
  uid: string;
  displayName: string;
  job: string | null;
  description: string | null;
  personality: string | null;
  teamId: string | null;
};

export type ProjectTeam = {
  id: string;
  name: string;
  agentIds: string[];
};

const migratedLegacyChannelProjects = new Set<string>();
const migratedLegacyDmKeys = new Set<string>();
const legacyParticipantRefCache = new Map<string, ParticipantRef>();
const chatApiBase = process.env.NEXT_PUBLIC_CHAT_API_BASE_URL ?? "http://localhost:5000";

function participantFieldKey(ref: ParticipantRef | string) {
  return String(ref || "").replace(/[^A-Za-z0-9_]/g, "_");
}

function readParticipantNumberMap(value: unknown) {
  if (!value || typeof value !== "object") return {} as Record<string, number>;

  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>)
      .map(([key, raw]) => [key, typeof raw === "number" ? raw : Number(raw) || 0]),
  );
}

function buildParticipantCounterSeed(participantIds: ParticipantRef[], initialValue = 0) {
  return Object.fromEntries(
    [...new Set(participantIds)].map((participantRef) => [participantFieldKey(participantRef), initialValue]),
  );
}

function normalizeAgentIdentity(data: DocumentData, agentId: string) {
  const job = (data.job as string | null) ?? (data.title as string | null) ?? null;
  const name = (data.name as string | null) ?? job ?? `Agent ${agentId.slice(0, 4)}`;
  const description = (data.description as string | null) ?? null;
  const personality = (data.personality as string | null) ?? null;
  const teamId = (data.teamId as string | null) ?? null;

  return { name, job, description, personality, teamId };
}



export function makeParticipantRef(kind: ParticipantKind, id: string): ParticipantRef {
  return `${kind}:${id}`;
}

export function parseParticipantRef(ref: ParticipantRef) {
  const [kind, ...rest] = ref.split(":");
  return {
    kind: kind as ParticipantKind,
    id: rest.join(":"),
  };
}

export function makeDmKey(participantIds: ParticipantRef[]) {
  return [...new Set(participantIds)].sort().join("|");
}

export function subscribeProjectConversations(
  projectId: string,
  cb: (conversations: Conversation[]) => void,
) {
  void migrateLegacyChannels(projectId);

  const q = query(
    collection(db, "conversations"),
    where("projectId", "==", projectId),
    orderBy("updatedAt", "desc"),
  );

  return onSnapshot(q, (snap) => {
    cb(snap.docs.map(toConversation));
  });
}

export async function createChannelConversation(
  projectId: string,
  title: string,
  participantIds: ParticipantRef[],
  createdBy: ParticipantRef,
) {
  return createConversation(projectId, "channel", title, participantIds, createdBy);
}

export async function createGroupConversation(
  projectId: string,
  title: string,
  participantIds: ParticipantRef[],
  createdBy: ParticipantRef,
) {
  return createConversation(projectId, "group", title, participantIds, createdBy);
}

export async function updateConversationParticipants(
  conversationId: string,
  participantIds: ParticipantRef[],
) {
  const normalizedParticipants = [...new Set(participantIds)].sort() as ParticipantRef[];
  const unreadSeed = buildParticipantCounterSeed(normalizedParticipants);

  await updateDoc(doc(db, "conversations", conversationId), {
    participantIds: normalizedParticipants,
    updatedAt: serverTimestamp(),
    ...Object.fromEntries(
      Object.keys(unreadSeed).map((key) => [`unreadCountByParticipant.${key}`, increment(0)]),
    ),
  });

  return normalizedParticipants;
}

export async function renameConversation(
  conversationId: string,
  title: string,
) {
  const nextTitle = title.trim();
  if (!nextTitle) return;

  await updateDoc(doc(db, "conversations", conversationId), {
    title: nextTitle,
    updatedAt: serverTimestamp(),
  });

  return nextTitle;
}

export async function deleteConversation(conversation: Conversation) {
  while (true) {
    const messagesSnap = await getDocs(
      query(collection(db, "conversations", conversation.id, "messages"), limit(200)),
    );

    if (messagesSnap.empty) break;

    const batch = writeBatch(db);
    for (const messageDoc of messagesSnap.docs) {
      batch.delete(doc(db, "conversations", conversation.id, "messages", messageDoc.id));
    }
    await batch.commit();
  }

  await deleteDoc(doc(db, "conversations", conversation.id));
}

export async function createOrGetDmConversation(
  projectId: string,
  participantIds: ParticipantRef[],
  createdBy: ParticipantRef,
) {
  const normalizedParticipants = [...new Set(participantIds)].sort() as ParticipantRef[];
  const dmKey = makeDmKey(normalizedParticipants);

  const existingQuery = query(
    collection(db, "conversations"),
    where("projectId", "==", projectId),
    where("kind", "==", "dm"),
    where("dmKey", "==", dmKey),
    limit(1),
  );

  const existingSnap = await getDocs(existingQuery);
  if (!existingSnap.empty) {
    const conversation = toConversation(existingSnap.docs[0]);
    await ensureLegacyDmMigrated(projectId, normalizedParticipants, conversation.id);
    return conversation;
  }

  const ref = await addDoc(collection(db, "conversations"), {
    projectId,
    kind: "dm",
    title: null,
    participantIds: normalizedParticipants,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
    lastMessageAt: serverTimestamp(),
    createdBy,
    dmKey,
    typingParticipantRefs: [],
    unreadCountByParticipant: buildParticipantCounterSeed(normalizedParticipants),
    lastSeenAtByParticipant: buildParticipantCounterSeed(normalizedParticipants),
  });

  await ensureLegacyDmMigrated(projectId, normalizedParticipants, ref.id);

  return {
    id: ref.id,
    projectId,
    kind: "dm",
    title: null,
    participantIds: normalizedParticipants,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    lastMessageAt: Date.now(),
    createdBy,
    dmKey,
    typingParticipantRefs: [],
    unreadCountByParticipant: buildParticipantCounterSeed(normalizedParticipants),
    lastSeenAtByParticipant: buildParticipantCounterSeed(normalizedParticipants),
  } satisfies Conversation;
}

export function subscribeConversationMessages(
  conversation: Conversation,
  cb: (messages: ChatMessage[]) => void,
) {
  void ensureLegacyMessagesMigrated(conversation);

  const q = query(
    collection(db, "conversations", conversation.id, "messages"),
    orderBy("createdAt", "asc"),
    limitToLast(100),
  );

  return onSnapshot(q, (snap) => {
    cb(snap.docs.map(toMessage));
  });
}

export async function sendConversationMessage(
  conversation: Pick<Conversation, "id" | "participantIds">,
  authorId: ParticipantRef,
  authorName: string,
  content: string,
  imageUrl?: string | null,
  videoUrl?: string | null,
  options?: {
    phase?: "final_answer" | "clarification";
    runId?: string | null;
    thoughtProcess?: string[];
  },
) {
  const messageRef = await addDoc(collection(db, "conversations", conversation.id, "messages"), {
    authorId,
    authorName,
    content,
    imageUrl: imageUrl ?? null,
    videoUrl: videoUrl ?? null,
    thoughtProcess: options?.thoughtProcess ?? null,
    phase: options?.phase ?? null,
    runId: options?.runId ?? null,
    createdAt: serverTimestamp(),
    seenBy: [authorId],
  });

  const unreadUpdates = Object.fromEntries(
    conversation.participantIds
      .filter((participantRef) => participantRef !== authorId)
      .map((participantRef) => [
        `unreadCountByParticipant.${participantFieldKey(participantRef)}`,
        increment(1),
      ]),
  );

  await updateDoc(doc(db, "conversations", conversation.id), {
    updatedAt: serverTimestamp(),
    lastMessageAt: serverTimestamp(),
    ...unreadUpdates,
  });

  return messageRef.id;
}

export async function setConversationTypingParticipant(
  conversationId: string,
  participantRef: ParticipantRef,
  isTyping: boolean,
) {
  await updateDoc(doc(db, "conversations", conversationId), {
    typingParticipantRefs: isTyping ? arrayUnion(participantRef) : arrayRemove(participantRef),
  });
}

export async function markConversationSeen(
  conversation: Pick<Conversation, "id" | "unreadCountByParticipant">,
  viewerRef: ParticipantRef,
  messages: ChatMessage[],
) {
  if (messages.length === 0) return;

  const visibleMessagesFromOthers = messages.filter((message) => message.authorId !== viewerRef);
  if (visibleMessagesFromOthers.length === 0) return;

  const unseenMessages = messages.filter(
    (message) => message.authorId !== viewerRef && !message.seenBy.includes(viewerRef),
  );
  const latestSeenAt = Math.max(...visibleMessagesFromOthers.map((message) => message.createdAt));

  const unreadKey = participantFieldKey(viewerRef);
  const currentUnreadCount = conversation.unreadCountByParticipant[unreadKey] ?? 0;
  if (unseenMessages.length === 0 && currentUnreadCount === 0) return;

  const batch = writeBatch(db);

  for (const message of unseenMessages) {
    batch.update(doc(db, "conversations", conversation.id, "messages", message.id), {
      seenBy: arrayUnion(viewerRef),
    });
  }

  batch.update(doc(db, "conversations", conversation.id), {
    [`lastSeenAtByParticipant.${unreadKey}`]: latestSeenAt,
    [`unreadCountByParticipant.${unreadKey}`]: 0,
  });

  await batch.commit();
}

export function getConversationUnreadCount(
  conversation: Pick<Conversation, "unreadCountByParticipant">,
  participantRef: ParticipantRef,
) {
  return Math.max(0, conversation.unreadCountByParticipant[participantFieldKey(participantRef)] ?? 0);
}

export async function updateConversationMessage(
  conversationId: string,
  messageId: string,
  content: string,
) {
  const nextContent = content.trim();
  if (!nextContent) return;

  await updateDoc(doc(db, "conversations", conversationId, "messages", messageId), {
    content: nextContent,
    updatedAt: serverTimestamp(),
  });

  await updateDoc(doc(db, "conversations", conversationId), {
    updatedAt: serverTimestamp(),
  });
}

export async function deleteConversationMessage(
  conversation: Conversation,
  messageId: string,
) {
  const messageRef = doc(db, "conversations", conversation.id, "messages", messageId);
  const messageSnap = await getDoc(messageRef);
  const messageData = messageSnap.data();
  const seenBy = Array.isArray(messageData?.seenBy)
    ? messageData?.seenBy.filter((value): value is ParticipantRef => typeof value === "string")
    : [];

  await deleteDoc(doc(db, "conversations", conversation.id, "messages", messageId));

  const latestRemainingSnap = await getDocs(
    query(
      collection(db, "conversations", conversation.id, "messages"),
      orderBy("createdAt", "desc"),
      limit(1),
    ),
  );

  const latestRemaining = latestRemainingSnap.docs[0];
  const lastMessageAt = latestRemaining ? toMillis(latestRemaining.data().createdAt) : conversation.createdAt;
  const unreadAdjustments = Object.fromEntries(
    conversation.participantIds
      .filter((participantRef) => participantRef !== (messageData?.authorId as ParticipantRef))
      .filter((participantRef) => !seenBy.includes(participantRef))
      .map((participantRef) => {
        const key = participantFieldKey(participantRef);
        const currentUnreadCount = Math.max(0, conversation.unreadCountByParticipant[key] ?? 0);
        return currentUnreadCount > 0
          ? [`unreadCountByParticipant.${key}`, currentUnreadCount - 1]
          : null;
      })
      .filter((entry): entry is [string, number] => Boolean(entry)),
  );

  await updateDoc(doc(db, "conversations", conversation.id), {
    updatedAt: serverTimestamp(),
    lastMessageAt,
    ...unreadAdjustments,
  });
}

export async function clearConversationHistory(conversation: Conversation) {
  const conversationRef = doc(db, "conversations", conversation.id);

  while (true) {
    const messagesSnap = await getDocs(
      query(collection(db, "conversations", conversation.id, "messages"), limit(200)),
    );

    if (messagesSnap.empty) break;

    const batch = writeBatch(db);
    for (const messageDoc of messagesSnap.docs) {
      batch.delete(doc(db, "conversations", conversation.id, "messages", messageDoc.id));
    }
    await batch.commit();
  }

  await updateDoc(conversationRef, {
    updatedAt: conversation.createdAt,
    lastMessageAt: conversation.createdAt,
    typingParticipantRefs: [],
    unreadCountByParticipant: buildParticipantCounterSeed(conversation.participantIds),
  });
}

function parseSseEvent(rawEvent: string) {
  if (!rawEvent.trim()) return null;

  let eventType = "message";
  const dataLines: string[] = [];

  for (const line of rawEvent.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (dataLines.length === 0) return null;

  try {
    return {
      eventType,
      data: JSON.parse(dataLines.join("\n")) as Record<string, unknown>,
    };
  } catch {
    return null;
  }
}

export async function streamConversationReply(
  payload: ChatCompletionRequest,
  handlers: StreamConversationReplyHandlers,
  options?: {
    signal?: AbortSignal;
  },
) {
  const response = await fetch(`${chatApiBase}/chat/respond/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
    signal: options?.signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat stream request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalReply: StreamedReply | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    while (true) {
      const boundary = buffer.indexOf("\n\n");
      if (boundary < 0) break;

      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const parsed = parseSseEvent(rawEvent);
      if (!parsed) continue;

      const { eventType, data } = parsed;
      if (eventType === "run.started") {
        handlers.onRunStarted?.({
          runId: String(data.runId ?? ""),
          status: String(data.status ?? "running"),
        });
        continue;
      }

      if (eventType === "node.entered") {
        handlers.onNodeEntered?.({
          node: String(data.node ?? ""),
        });
        continue;
      }

      if (eventType === "commentary.delta") {
        handlers.onCommentaryDelta?.({
          node: String(data.node ?? ""),
          textDelta: String(data.textDelta ?? ""),
        });
        continue;
      }

      if (eventType === "commentary.completed") {
        handlers.onCommentaryCompleted?.({
          node: String(data.node ?? ""),
          text: String(data.text ?? ""),
          statusText: typeof data.statusText === "string" ? data.statusText : undefined,
        });
        continue;
      }

      if (eventType === "tool.started" || eventType === "tool.completed" || eventType === "tool.failed") {
        handlers.onToolEvent?.({
          node: typeof data.node === "string" ? data.node : undefined,
          toolName: String(data.toolName ?? ""),
          callId: String(data.callId ?? ""),
          args: data.args,
          output: data.output,
          error: typeof data.error === "string" ? data.error : undefined,
          status:
            eventType === "tool.started"
              ? "started"
              : eventType === "tool.completed"
                ? "completed"
                : "failed",
        });
        continue;
      }

      if (eventType === "clarification.requested") {
        handlers.onClarificationRequested?.({
          content: String(data.content ?? ""),
          phase: "clarification",
          runId: String(data.runId ?? ""),
        });
        continue;
      }

      if (eventType === "final.delta") {
        handlers.onFinalDelta?.({
          textDelta: String(data.textDelta ?? ""),
        });
        continue;
      }

      if (eventType === "final.completed") {
        handlers.onFinalCompleted?.({
          content: String(data.content ?? ""),
          phase: "final_answer",
        });
        continue;
      }

      if (eventType === "run.completed") {
        finalReply = {
          content: String(data.content ?? "").trim(),
          imageUrl: typeof data.imageUrl === "string" ? data.imageUrl : null,
          videoUrl: typeof data.videoUrl === "string" ? data.videoUrl : null,
          requestedAgentRefs: Array.isArray(data.requestedAgentRefs)
            ? data.requestedAgentRefs.filter((value): value is string => typeof value === "string")
            : [],
          handoffReason: String(data.handoffReason ?? ""),
          handoffPrompt: String(data.handoffPrompt ?? ""),
          phase: data.phase === "clarification" ? "clarification" : "final_answer",
          runId: String(data.runId ?? ""),
          waitingForUser: String(data.status ?? "") === "waiting_for_user",
        };
        continue;
      }

      if (eventType === "run.failed") {
        throw new Error(String(data.error ?? data.content ?? "Streaming reply failed."));
      }
    }
  }

  if (!finalReply) {
    throw new Error("Chat stream ended before a final payload was received.");
  }

  return finalReply;
}

export async function stopConversationReply(payload: StopConversationReplyRequest) {
  const response = await fetch(`${chatApiBase}/chat/respond/stop`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Stop stream request failed with status ${response.status}`);
  }

  return response.json() as Promise<{ stopped: boolean; runId: string }>;
}

export async function moderateChannelResponders(payload: ModeratorRequest) {
  const response = await fetch(`${chatApiBase}/ghosts/moderator/responders`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Moderator API request failed with status ${response.status}`);
  }

  const data = (await response.json()) as { agentRefs?: string[] };
  return data.agentRefs ?? [];
}

export async function listConversationMessages(conversation: Conversation) {
  await ensureLegacyMessagesMigrated(conversation);

  const snap = await getDocs(
    query(
      collection(db, "conversations", conversation.id, "messages"),
      orderBy("createdAt", "asc"),
    ),
  );

  return snap.docs.map(toMessage);
}

export function subscribeProjectTeams(
  projectId: string,
  cb: (teams: ProjectTeam[]) => void,
) {
  const q = query(
    collection(db, "teams"),
    where("projectIds", "array-contains", projectId),
  );

  return onSnapshot(q, (snap) => {
    cb(
      snap.docs
        .map((d) => {
          const data = d.data();
          return {
            id: d.id,
            name: (data.name as string) ?? "",
            agentIds: Array.isArray(data.agentIds) ? data.agentIds : [],
          };
        })
        .sort((a, b) => a.name.localeCompare(b.name)),
    );
  });
}

export function subscribeProjectParticipants(
  projectId: string,
  currentUserId: string,
  cb: (participants: ResolvedParticipant[]) => void,
) {
  let currentUsers: Member[] = [];
  let currentAgents: AgentMember[] = [];
  let stopUsers = () => {};
  let stopAgents = () => {};

  const publish = () => {
    cb(
      [
        ...currentUsers.map((member) => ({
          ref: makeParticipantRef("user", member.uid),
          sourceId: member.uid,
          kind: "user" as const,
          label: member.displayName ?? member.email ?? member.uid,
          secondaryLabel: member.email ?? null,
          description: null,
          personality: null,
          teamId: null,
        })),
        ...currentAgents.map((agent) => ({
          ref: makeParticipantRef("agent", agent.uid),
          sourceId: agent.uid,
          kind: "agent" as const,
          label: agent.displayName,
          secondaryLabel: agent.job,
          description: agent.description,
          personality: agent.personality,
          teamId: agent.teamId,
        })),
      ].sort((a, b) => a.label.localeCompare(b.label)),
    );
  };

  const stopTeams = subscribeProjectTeams(projectId, (teams) => {
    const teamIds = teams.map((team) => team.id);
    const agentIds = [...new Set(teams.flatMap((team) => team.agentIds))];

    stopUsers();
    stopAgents();

    currentUsers = [];
    currentAgents = [];
    publish();

    stopUsers = subscribeProjectMembers(teamIds, currentUserId, (members) => {
      currentUsers = members;
      publish();
    });

    stopAgents = subscribeProjectAgents(agentIds, (agents) => {
      currentAgents = agents;
      publish();
    });
  });

  return () => {
    stopUsers();
    stopAgents();
    stopTeams();
  };
}

export function subscribeResolvedParticipants(
  participantRefs: ParticipantRef[],
  cb: (participants: ResolvedParticipant[]) => void,
) {
  if (participantRefs.length === 0) {
    cb([]);
    return () => {};
  }

  const uniqueRefs = [...new Set(participantRefs)];
  const userIds = uniqueRefs
    .filter((ref): ref is `user:${string}` => ref.startsWith("user:"))
    .map((ref) => parseParticipantRef(ref).id);
  const agentIds = uniqueRefs
    .filter((ref): ref is `agent:${string}` => ref.startsWith("agent:"))
    .map((ref) => parseParticipantRef(ref).id);

  const cache = new Map<ParticipantRef, ResolvedParticipant>();
  const unsubs: Array<() => void> = [];

  const publish = () => {
    cb(
      uniqueRefs
        .map((ref) => cache.get(ref))
        .filter((participant): participant is ResolvedParticipant => Boolean(participant)),
    );
  };

  for (const chunk of chunkIds(userIds)) {
    if (chunk.length === 0) continue;

    unsubs.push(
      onSnapshot(
        query(collection(db, "users"), where(documentId(), "in", chunk)),
        (snap) => {
          for (const id of chunk) {
            cache.delete(makeParticipantRef("user", id));
          }

          for (const userDoc of snap.docs) {
            const data = userDoc.data();
            const ref = makeParticipantRef("user", userDoc.id);
            cache.set(ref, {
              ref,
              sourceId: userDoc.id,
              kind: "user",
              label: (data.displayName as string | null) ?? (data.email as string | null) ?? userDoc.id,
              secondaryLabel: (data.email as string | null) ?? null,
              description: null,
              personality: null,
              teamId: null,
            });
          }

          publish();
        },
      ),
    );
  }

  for (const chunk of chunkIds(agentIds)) {
    if (chunk.length === 0) continue;

    unsubs.push(
      onSnapshot(
        query(collection(db, "agents"), where(documentId(), "in", chunk)),
        (snap) => {
          for (const id of chunk) {
            cache.delete(makeParticipantRef("agent", id));
          }

          for (const agentDoc of snap.docs) {
            const data = agentDoc.data();
            const agent = normalizeAgentIdentity(data, agentDoc.id);
            const ref = makeParticipantRef("agent", agentDoc.id);
            cache.set(ref, {
              ref,
              sourceId: agentDoc.id,
              kind: "agent",
              label: agent.name,
              secondaryLabel: agent.job,
              description: agent.description,
              personality: agent.personality,
              teamId: agent.teamId,
            });
          }

          publish();
        },
      ),
    );
  }

  return () => unsubs.forEach((unsub) => unsub());
}

export function subscribeProjectMembers(
  teamIds: string[],
  currentUserId: string,
  cb: (members: Member[]) => void,
) {
  if (teamIds.length === 0) {
    cb([]);
    return () => {};
  }

  const q = query(
    collection(db, "users"),
    where("teamIds", "array-contains-any", teamIds.slice(0, 30)),
  );

  return onSnapshot(q, (snap) => {
    cb(
      snap.docs
        .filter((d) => d.id !== currentUserId)
        .map((d) => {
          const data = d.data();
          return {
            uid: d.id,
            displayName: data.displayName ?? null,
            email: data.email ?? null,
          };
        })
        .sort((a, b) => getMemberLabel(a).localeCompare(getMemberLabel(b))),
    );
  });
}

export function subscribeProjectAgents(
  agentIds: string[],
  cb: (agents: AgentMember[]) => void,
) {
  if (agentIds.length === 0) {
    cb([]);
    return () => {};
  }

  const cache = new Map<string, AgentMember>();
  const unsubs = chunkIds(agentIds).map((chunk) =>
    onSnapshot(
      query(collection(db, "agents"), where(documentId(), "in", chunk)),
      (snap) => {
        for (const agentId of chunk) {
          cache.delete(agentId);
        }

        for (const agentDoc of snap.docs) {
          const data = agentDoc.data();
          const agent = normalizeAgentIdentity(data, agentDoc.id);
          cache.set(agentDoc.id, {
            uid: agentDoc.id,
            displayName: agent.name,
            job: agent.job,
            description: agent.description,
            personality: agent.personality,
            teamId: agent.teamId,
          });
        }

        cb(
          agentIds
            .map((agentId) => cache.get(agentId))
            .filter((agent): agent is AgentMember => Boolean(agent))
            .sort((a, b) => a.displayName.localeCompare(b.displayName)),
        );
      },
    ),
  );

  return () => unsubs.forEach((unsub) => unsub());
}

async function createConversation(
  projectId: string,
  kind: Exclude<ConversationKind, "dm">,
  title: string,
  participantIds: ParticipantRef[],
  createdBy: ParticipantRef,
) {
  const normalizedParticipants = [...new Set(participantIds)].sort() as ParticipantRef[];
  const ref = await addDoc(collection(db, "conversations"), {
    projectId,
    kind,
    title,
    participantIds: normalizedParticipants,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
    lastMessageAt: serverTimestamp(),
    createdBy,
    dmKey: null,
    typingParticipantRefs: [],
    unreadCountByParticipant: buildParticipantCounterSeed(normalizedParticipants),
    lastSeenAtByParticipant: buildParticipantCounterSeed(normalizedParticipants),
  });

  return {
    id: ref.id,
    projectId,
    kind,
    title,
    participantIds: normalizedParticipants,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    lastMessageAt: Date.now(),
    createdBy,
    dmKey: null,
    typingParticipantRefs: [],
    unreadCountByParticipant: buildParticipantCounterSeed(normalizedParticipants),
    lastSeenAtByParticipant: buildParticipantCounterSeed(normalizedParticipants),
  } satisfies Conversation;
}

async function migrateLegacyChannels(projectId: string) {
  if (migratedLegacyChannelProjects.has(projectId)) return;
  migratedLegacyChannelProjects.add(projectId);

  const legacyChannels = await getDocs(collection(db, "projects", projectId, "channels"));
  if (legacyChannels.empty) return;

  const participantIds = await getProjectParticipantRefs(projectId);

  for (const channelDoc of legacyChannels.docs) {
    const data = channelDoc.data();
    const conversationId = legacyChannelConversationId(projectId, channelDoc.id);

    await setDoc(
      doc(db, "conversations", conversationId),
      {
        projectId,
        kind: "channel",
        title: (data.name as string) ?? "Untitled channel",
        participantIds,
        createdAt: data.createdAt ?? serverTimestamp(),
        updatedAt: data.createdAt ?? serverTimestamp(),
        lastMessageAt: data.createdAt ?? serverTimestamp(),
        createdBy: null,
        dmKey: null,
        typingParticipantRefs: [],
        unreadCountByParticipant: buildParticipantCounterSeed(participantIds),
        lastSeenAtByParticipant: buildParticipantCounterSeed(participantIds),
      },
      { merge: true },
    );

    await migrateLegacyMessages(
      collection(db, "projects", projectId, "channels", channelDoc.id, "messages"),
      conversationId,
    );
  }
}

async function ensureLegacyMessagesMigrated(conversation: Conversation) {
  if (conversation.kind === "channel" && conversation.id.startsWith("legacy-channel:")) {
    const legacyChannelId = conversation.id.replace(`legacy-channel:${conversation.projectId}:`, "");
    await migrateLegacyMessages(
      collection(db, "projects", conversation.projectId, "channels", legacyChannelId, "messages"),
      conversation.id,
    );
    return;
  }

  if (conversation.kind === "dm") {
    await ensureLegacyDmMigrated(conversation.projectId, conversation.participantIds, conversation.id);
  }
}

async function ensureLegacyDmMigrated(
  projectId: string,
  participantIds: ParticipantRef[],
  conversationId: string,
) {
  const legacyDmKey = `${projectId}:${makeDmKey(participantIds)}`;
  if (migratedLegacyDmKeys.has(legacyDmKey)) return;
  migratedLegacyDmKeys.add(legacyDmKey);

  const rawDmId = [...new Set(participantIds)]
    .map((ref) => parseParticipantRef(ref).id)
    .sort()
    .join("_");

  await migrateLegacyMessages(
    collection(db, "projects", projectId, "dms", rawDmId, "messages"),
    conversationId,
  );
}

async function migrateLegacyMessages(
  legacyCollection: ReturnType<typeof collection>,
  conversationId: string,
) {
  const legacyMessages = await getDocs(query(legacyCollection, orderBy("createdAt", "asc")));
  if (legacyMessages.empty) return;

  const destination = collection(db, "conversations", conversationId, "messages");
  const chunks = chunkDocs(legacyMessages.docs, 200);

  for (const docsChunk of chunks) {
    const batch = writeBatch(db);

    for (const legacyDoc of docsChunk) {
      const data = legacyDoc.data();
      batch.set(doc(destination, legacyDoc.id), {
        authorId: await resolveLegacyAuthorRef((data.authorId as string) ?? ""),
        authorName: (data.authorName as string) ?? "Unknown",
        content: (data.content as string) ?? "",
        createdAt: data.createdAt ?? serverTimestamp(),
        seenBy: [await resolveLegacyAuthorRef((data.authorId as string) ?? "")],
      }, { merge: true });
    }

    batch.update(doc(db, "conversations", conversationId), {
      updatedAt: serverTimestamp(),
      lastMessageAt: serverTimestamp(),
    });

    await batch.commit();
  }
}

async function getProjectParticipantRefs(projectId: string) {
  const teamsSnap = await getDocs(
    query(collection(db, "teams"), where("projectIds", "array-contains", projectId)),
  );

  const teamIds = teamsSnap.docs.map((teamDoc) => teamDoc.id);
  const agentIds = [...new Set(
    teamsSnap.docs.flatMap((teamDoc) => {
      const data = teamDoc.data();
      return Array.isArray(data.agentIds) ? data.agentIds : [];
    }),
  )];

  const participantIds: ParticipantRef[] = [];

  if (teamIds.length > 0) {
    const usersSnap = await getDocs(
      query(collection(db, "users"), where("teamIds", "array-contains-any", teamIds.slice(0, 30))),
    );

    for (const userDoc of usersSnap.docs) {
      participantIds.push(makeParticipantRef("user", userDoc.id));
    }
  }

  for (const chunk of chunkIds(agentIds)) {
    if (chunk.length === 0) continue;
    const agentsSnap = await getDocs(
      query(collection(db, "agents"), where(documentId(), "in", chunk)),
    );

    for (const agentDoc of agentsSnap.docs) {
      participantIds.push(makeParticipantRef("agent", agentDoc.id));
    }
  }

  return [...new Set(participantIds)].sort() as ParticipantRef[];
}

async function resolveLegacyAuthorRef(authorId: string) {
  if (!authorId) return "user:unknown" as ParticipantRef;
  if (authorId === "bot-system") return makeParticipantRef("agent", "archibot");

  const cached = legacyParticipantRefCache.get(authorId);
  if (cached) return cached;

  const userSnap = await getDoc(doc(db, "users", authorId));
  if (userSnap.exists()) {
    const ref = makeParticipantRef("user", authorId);
    legacyParticipantRefCache.set(authorId, ref);
    return ref;
  }

  const agentSnap = await getDoc(doc(db, "agents", authorId));
  if (agentSnap.exists()) {
    const ref = makeParticipantRef("agent", authorId);
    legacyParticipantRefCache.set(authorId, ref);
    return ref;
  }

  const fallback = makeParticipantRef("user", authorId);
  legacyParticipantRefCache.set(authorId, fallback);
  return fallback;
}

function legacyChannelConversationId(projectId: string, channelId: string) {
  return `legacy-channel:${projectId}:${channelId}`;
}

function toConversation(docSnap: QueryDocumentSnapshot<DocumentData>): Conversation {
  const data = docSnap.data();
  return {
    id: docSnap.id,
    projectId: (data.projectId as string) ?? "",
    kind: (data.kind as ConversationKind) ?? "channel",
    title: (data.title as string | null) ?? null,
    participantIds: Array.isArray(data.participantIds)
      ? (data.participantIds.filter((value): value is ParticipantRef => typeof value === "string") as ParticipantRef[])
      : [],
    createdAt: toMillis(data.createdAt),
    updatedAt: toMillis(data.updatedAt),
    lastMessageAt: toMillis(data.lastMessageAt),
    createdBy: (data.createdBy as ParticipantRef | null) ?? null,
    dmKey: (data.dmKey as string | null) ?? null,
    typingParticipantRefs: Array.isArray(data.typingParticipantRefs)
      ? data.typingParticipantRefs.filter((value): value is ParticipantRef => typeof value === "string")
      : [],
    unreadCountByParticipant: readParticipantNumberMap(data.unreadCountByParticipant),
    lastSeenAtByParticipant: readParticipantNumberMap(data.lastSeenAtByParticipant),
  };
}

function toMillis(value: unknown): number {
  if (value instanceof Timestamp) return value.toMillis();
  if (typeof value === "number") return value;
  return Date.now();
}

function toMessage(docSnap: QueryDocumentSnapshot<DocumentData>): ChatMessage {
  const data = docSnap.data();
  return {
    id: docSnap.id,
    authorId: (data.authorId as string) ?? "",
    authorName: (data.authorName as string) ?? "",
    content: (data.content as string) ?? "",
    imageUrl: (data.imageUrl as string | null) ?? null,
    videoUrl: (data.videoUrl as string | null) ?? null,
    thoughtProcess: Array.isArray(data.thoughtProcess)
      ? data.thoughtProcess.filter((value): value is string => typeof value === "string" && value.trim().length > 0)
      : null,
    phase: (data.phase as "final_answer" | "clarification" | null) ?? null,
    runId: (data.runId as string | null) ?? null,
    createdAt: toMillis(data.createdAt),
    seenBy: Array.isArray(data.seenBy)
      ? data.seenBy.filter((value): value is ParticipantRef => typeof value === "string")
      : [],
  };
}

function getMemberLabel(member: Member) {
  return member.displayName?.trim() || member.email?.trim() || member.uid;
}

function chunkIds(ids: string[], size = 30) {
  const chunks: string[][] = [];

  for (let index = 0; index < ids.length; index += size) {
    chunks.push(ids.slice(index, index + size));
  }

  return chunks;
}

function chunkDocs<T>(docs: T[], size: number) {
  const chunks: T[][] = [];

  for (let index = 0; index < docs.length; index += size) {
    chunks.push(docs.slice(index, index + size));
  }

  return chunks;
}
