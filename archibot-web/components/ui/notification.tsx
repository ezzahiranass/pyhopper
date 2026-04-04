"use client";

import * as React from "react";
import { X, CheckCircle2, AlertCircle, Info, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type NotificationVariant = "info" | "success" | "error" | "loading";

export type NotificationItem = {
  id: string;
  variant: NotificationVariant;
  title: string;
  description?: string;
};

const ICONS: Record<NotificationVariant, React.ReactNode> = {
  info: <Info size={16} />,
  success: <CheckCircle2 size={16} />,
  error: <AlertCircle size={16} />,
  loading: <Loader2 size={16} className="animate-spin" />,
};

const STYLES: Record<NotificationVariant, string> = {
  info: "bg-card border-border text-foreground",
  success: "bg-card border-emerald-200 text-foreground",
  error: "bg-card border-destructive/30 text-foreground",
  loading: "bg-card border-blue-200 text-foreground",
};

const ICON_STYLES: Record<NotificationVariant, string> = {
  info: "text-muted-foreground",
  success: "text-emerald-600",
  error: "text-destructive",
  loading: "text-blue-500",
};

function Notification({
  item,
  onDismiss,
}: {
  item: NotificationItem;
  onDismiss: (id: string) => void;
}) {
  const isDismissable = item.variant !== "loading";

  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-3 rounded-xl border px-4 py-3 shadow-md text-sm w-80 animate-in slide-in-from-right-4 fade-in duration-200",
        STYLES[item.variant],
      )}
    >
      <span className={cn("mt-0.5 shrink-0", ICON_STYLES[item.variant])}>
        {ICONS[item.variant]}
      </span>
      <div className="flex-1 min-w-0">
        <p className="font-medium leading-snug">{item.title}</p>
        {item.description && (
          <p className="text-muted-foreground mt-0.5 leading-snug">{item.description}</p>
        )}
      </div>
      {isDismissable && (
        <button
          onClick={() => onDismiss(item.id)}
          className="shrink-0 mt-0.5 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Dismiss"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

export function NotificationTray({
  notifications,
  onDismiss,
}: {
  notifications: NotificationItem[];
  onDismiss: (id: string) => void;
}) {
  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 items-end pointer-events-none">
      {notifications.map((item) => (
        <div key={item.id} className="pointer-events-auto">
          <Notification item={item} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  );
}
