"use client";

import { useEffect, useState } from "react";
import {
  Check,
  ChevronDown,
  ChevronRight,
  Copy,
  EllipsisVertical,
  Info,
  Pencil,
  Trash2,
  X,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import type { ChatMessage } from "./chat-service";

interface MessageProps {
  message: ChatMessage;
  showHeader: boolean;
  currentUserId: string;
  authorJobTitle?: string | null;
  onShowInfo?: (message: ChatMessage) => void;
  onEditMessage?: (message: ChatMessage, content: string) => Promise<void> | void;
  onDeleteMessage?: (message: ChatMessage) => Promise<void> | void;
  activeInfoMessageId?: string | null;
}

interface TypingMessageProps {
  authors: Array<{
    id: string;
    name: string;
  }>;
}

interface StreamingMessageProps {
  authorId: string;
  authorName: string;
  authorJobTitle?: string | null;
  statusLabel?: string;
  thoughtProcess: string[];
  commentary: string;
  finalText: string;
  toolEvents: Array<{
    node?: string;
    toolName: string;
    status: "started" | "completed" | "failed";
  }>;
}

const AVATAR_COLORS = [
  "#6366f1", "#0ea5e9", "#f59e0b", "#10b981", "#ec4899",
  "#8b5cf6", "#14b8a6", "#f97316", "#06b6d4", "#e11d48",
];

function colorFor(id: string) {
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) | 0;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function initials(name: string) {
  const parts = name.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

function formatTime(ms: number) {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDateTime(ms: number) {
  return new Date(ms).toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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

function truncatePreview(text: string, maxLength = 96, keepTail = false) {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized) return "";
  if (normalized.length <= maxLength) return normalized;
  if (keepTail) {
    return `...${normalized.slice(-(maxLength - 3)).trimStart()}`;
  }
  return `${normalized.slice(0, maxLength - 3).trimEnd()}...`;
}

type MediaLightboxState =
  | { kind: "image"; url: string }
  | { kind: "video"; url: string }
  | null;

function MessageMedia({
  imageUrl,
  videoUrl,
}: {
  imageUrl?: string | null;
  videoUrl?: string | null;
}) {
  const [lightbox, setLightbox] = useState<MediaLightboxState>(null);

  useEffect(() => {
    if (!lightbox) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setLightbox(null);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [lightbox]);

  if (!imageUrl && !videoUrl) return null;

  return (
    <>
      {imageUrl ? (
        <button
          type="button"
          className="chat-message__media-button"
          onClick={() => setLightbox({ kind: "image", url: imageUrl })}
          aria-label="Open image"
        >
          <img
            className="chat-message__media"
            src={imageUrl}
            alt="Generated architectural visualization"
          />
        </button>
      ) : null}
      {videoUrl ? (
        <button
          type="button"
          className="chat-message__media-button"
          onClick={() => setLightbox({ kind: "video", url: videoUrl })}
          aria-label="Open video"
        >
          <video
            className="chat-message__media"
            src={videoUrl}
            muted
            playsInline
            preload="metadata"
          />
        </button>
      ) : null}

      {lightbox ? (
        <div className="chat-media-lightbox" onClick={() => setLightbox(null)}>
          <button
            type="button"
            className="chat-media-lightbox__close"
            onClick={() => setLightbox(null)}
            aria-label="Close preview"
          >
            <X size={18} />
          </button>
          <div className="chat-media-lightbox__content" onClick={(event) => event.stopPropagation()}>
            {lightbox.kind === "image" ? (
              <img
                className="chat-media-lightbox__media"
                src={lightbox.url}
                alt="Generated architectural visualization"
              />
            ) : (
              <video
                className="chat-media-lightbox__media"
                src={lightbox.url}
                controls
                autoPlay
                playsInline
              />
            )}
          </div>
        </div>
      ) : null}
    </>
  );
}

function MarkdownMessage({
  content,
  commentary = false,
  compact = false,
}: {
  content: string;
  commentary?: boolean;
  compact?: boolean;
}) {
  return (
    <div className={`chat-message__text${commentary ? " chat-message__text--commentary" : ""}${compact ? " chat-message__text--compact" : ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: (props) => (
            <a {...props} target="_blank" rel="noreferrer noopener" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function ThoughtProcessBlock({
  summary,
  steps,
  preview,
  commentary,
}: {
  summary: string;
  steps: string[];
  preview?: string;
  commentary?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  if (steps.length <= 1) return null;

  const collapsedLabel = truncatePreview(preview || summary, 96, Boolean(commentary?.trim())) || "Thought Process";

  return (
    <details
      style={{ marginTop: 8, marginBottom: 8 }}
      open={isOpen}
      onToggle={(event) => setIsOpen((event.currentTarget as HTMLDetailsElement).open)}
      className="chat-message__thoughts"
    >
      <summary className="chat-message__thoughts-summary">
        {isOpen ? <ChevronDown size={14} strokeWidth={1.8} /> : <ChevronRight size={14} strokeWidth={1.8} />}
        <span>{isOpen ? "Thought Process" : collapsedLabel}</span>
      </summary>
      <div className="chat-message__thoughts-body">
        {steps.map((step, index) => (
          <div key={`${summary}-${index}`} className="chat-message__thoughts-step">
            <MarkdownMessage content={step} commentary compact />
          </div>
        ))}
        {commentary?.trim() ? (
          <div className="chat-message__thoughts-commentary">
            <MarkdownMessage content={commentary} commentary compact />
          </div>
        ) : null}
      </div>
    </details>
  );
}

export function Message({
  message,
  showHeader,
  currentUserId,
  authorJobTitle,
  onShowInfo,
  onEditMessage,
  onDeleteMessage,
  activeInfoMessageId,
}: MessageProps) {
  const isOwn = message.authorId === currentUserId;
  const color = isOwn ? "#111111" : colorFor(message.authorId);
  const [menuOpen, setMenuOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(message.content);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [copied, setCopied] = useState(false);
  const showPinnedInfo = activeInfoMessageId === message.id;

  useEffect(() => {
    setDraft(message.content);
    setIsEditing(false);
    setIsSaving(false);
    setIsDeleting(false);
  }, [message.content, message.id]);

  useEffect(() => {
    if (!copied) return;
    const timeoutId = window.setTimeout(() => setCopied(false), 1500);
    return () => window.clearTimeout(timeoutId);
  }, [copied]);

  async function handleSaveEdit() {
    const nextDraft = draft.trim();
    if (!nextDraft || nextDraft === message.content.trim() || !onEditMessage) {
      setIsEditing(false);
      setDraft(message.content);
      return;
    }

    setIsSaving(true);
    try {
      await onEditMessage(message, nextDraft);
      setIsEditing(false);
      setMenuOpen(false);
    } catch (error) {
      console.error("Failed to edit message", error);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    if (!onDeleteMessage) return;

    setIsDeleting(true);
    try {
      await onDeleteMessage(message);
      setMenuOpen(false);
    } catch (error) {
      console.error("Failed to delete message", error);
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
    } catch (error) {
      console.error("Failed to copy message", error);
    }
  }

  return (
    <div className="chat-message" data-own={isOwn}>
      {showHeader ? (
        <div className="chat-message__avatar" style={{ background: color }}>
          {initials(message.authorName)}
        </div>
      ) : (
        <div className="chat-message__avatar-gap" />
      )}
      <div className="chat-message__body">
        <div className="chat-message__actions">
          {copied ? (
            <span className="chat-message__copy-feedback" role="status" aria-live="polite">
              Message Copied to Clipboard
            </span>
          ) : null}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label={copied ? "Message copied" : "Copy message"}
            title={copied ? "Copied" : "Copy message"}
            onClick={() => void handleCopy()}
          >
            {copied ? (
              <Check size={24} color="#0f172a" absoluteStrokeWidth />
            ) : (
              <Copy size={24} color="#0f172a" absoluteStrokeWidth />
            )}
          </Button>
          <Popover open={menuOpen} onOpenChange={setMenuOpen}>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label="Message actions"
                title="Message actions"
              >
                <EllipsisVertical size={24} color="#0f172a" absoluteStrokeWidth />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="chat-message__menu" sideOffset={6}>
              <button
                type="button"
                className="chat-message__menu-item"
                onClick={() => {
                  onShowInfo?.(message);
                  setMenuOpen(false);
                }}
              >
                <Info size={14} />
                <span>Info</span>
              </button>
              <button
                type="button"
                className="chat-message__menu-item"
                onClick={() => {
                  setDraft(message.content);
                  setIsEditing(true);
                  setMenuOpen(false);
                }}
              >
                <Pencil size={14} />
                <span>Edit message</span>
              </button>
              <button
                type="button"
                className="chat-message__menu-item chat-message__menu-item--danger"
                onClick={() => void handleDelete()}
                disabled={isDeleting}
              >
                <Trash2 size={14} />
                <span>{isDeleting ? "Deleting..." : "Delete"}</span>
              </button>
            </PopoverContent>
          </Popover>
        </div>
        {showHeader && (
          <div className="chat-message__header">
            <div className="chat-message__author">
              <span className="chat-message__name">{message.authorName}</span>
              {authorJobTitle ? (
                <span className="chat-message__job-title">{authorJobTitle}</span>
              ) : null}
              {message.phase === "clarification" ? (
                <span className="chat-message__job-title">Awaiting clarification</span>
              ) : null}
            </div>
            <span className="chat-message__time">{formatTime(message.createdAt)}</span>
          </div>
        )}
        <ThoughtProcessBlock
          summary="Thought Process"
          steps={message.thoughtProcess ?? []}
          preview="Thought Process"
        />
        {isEditing ? (
          <div className="chat-message__editor">
            <Textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              className="chat-message__editor-input"
              rows={3}
            />
            <div className="chat-message__editor-actions">
              <Button
                type="button"
                size="sm"
                className="chat-message__editor-btn"
                onClick={() => void handleSaveEdit()}
                disabled={isSaving || !draft.trim()}
              >
                {isSaving ? "Saving..." : <><Check size={14} /> Save</>}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="chat-message__editor-btn chat-message__editor-btn--ghost"
                onClick={() => {
                  setDraft(message.content);
                  setIsEditing(false);
                }}
                disabled={isSaving}
              >
                <X size={14} /> Cancel
              </Button>
            </div>
          </div>
        ) : (
          <MarkdownMessage content={message.content} />
        )}
        <MessageMedia imageUrl={message.imageUrl} videoUrl={message.videoUrl} />
        <div
          className={`chat-message__meta${showPinnedInfo ? " chat-message__meta--visible" : ""}`}
          aria-label={`Sent ${formatDateTime(message.createdAt)}`}
        >
          {formatDateTime(message.createdAt)}
        </div>
      </div>
    </div>
  );
}

export function StreamingMessage({
  authorId,
  authorName,
  authorJobTitle,
  statusLabel,
  thoughtProcess,
  commentary,
  finalText,
  toolEvents,
}: StreamingMessageProps) {
  const color = colorFor(authorId);
  const latestToolEvent = toolEvents.length > 0 ? toolEvents[toolEvents.length - 1] : null;

  return (
    <div className="chat-message chat-message--streaming">
      <div className="chat-message__avatar" style={{ background: color }}>
        {initials(authorName)}
      </div>
      <div className="chat-message__body">
        <div className="chat-message__header">
          <div className="chat-message__author">
            <span className="chat-message__name">{authorName}</span>
            {authorJobTitle ? (
              <span className="chat-message__job-title">{authorJobTitle}</span>
            ) : null}
          </div>
          <span className="chat-message__time">live</span>
        </div>
        <ThoughtProcessBlock
          summary={statusLabel || "Thinking"}
          steps={thoughtProcess}
          preview={commentary || thoughtProcess[thoughtProcess.length - 1] || statusLabel || "Thinking"}
          commentary={commentary}
        />
        {latestToolEvent ? (
          <div className="chat-message__tool-list">
            <div className="chat-message__tool-pill">
              <span>
                Used Tool:{" "}
                {formatTraceNode(latestToolEvent.node)
                  ? `${formatTraceNode(latestToolEvent.node)}: ${latestToolEvent.toolName.replaceAll("_", " ")}`
                  : latestToolEvent.toolName.replaceAll("_", " ")}
              </span>
            </div>
          </div>
        ) : null}
        {finalText ? <MarkdownMessage content={finalText} /> : null}
        {!commentary && !finalText && toolEvents.length === 0 ? (
          <div className="chat-message__typing" aria-label={`${authorName} is thinking`}>
            <span className="chat-message__typing-dot" />
            <span className="chat-message__typing-dot" />
            <span className="chat-message__typing-dot" />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function getTypingLabel(authors: TypingMessageProps["authors"]) {
  if (authors.length === 0) return "";
  if (authors.length === 1) return `${authors[0].name} is typing`;
  const others = authors.length - 1;
  return `${authors[0].name} and ${others} ${others === 1 ? "other" : "others"} are typing`;
}

export function TypingMessage({ authors }: TypingMessageProps) {
  if (authors.length === 0) return null;

  const leadAuthor = authors[0];

  return (
    <div className="chat-message chat-message--typing">
      <div className="chat-message__avatar" style={{ background: colorFor(leadAuthor.id) }}>
        {authors.length === 1 ? initials(leadAuthor.name) : `${authors.length}`}
      </div>
      <div className="chat-message__body">
        <div className="chat-message__header">
          <span className="chat-message__name">{getTypingLabel(authors)}</span>
          <span className="chat-message__typing-label">typing</span>
        </div>
        <div className="chat-message__typing" aria-label={getTypingLabel(authors)}>
          <span className="chat-message__typing-dot" />
          <span className="chat-message__typing-dot" />
          <span className="chat-message__typing-dot" />
        </div>
      </div>
    </div>
  );
}
