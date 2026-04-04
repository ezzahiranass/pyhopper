"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type WorkspaceArtifactViewerContextValue = {
  activeInstanceId: string | null;
  optimizeEmbeds: boolean;
  isViewerActive: (instanceId: string) => boolean;
  setActiveInstanceId: (instanceId: string | null) => void;
};

const WorkspaceArtifactViewerContext = createContext<WorkspaceArtifactViewerContextValue | null>(null);

export function WorkspaceArtifactViewerProvider({
  optimizeEmbeds,
  children,
}: {
  optimizeEmbeds: boolean;
  children: ReactNode;
}) {
  const [activeInstanceId, setActiveInstanceId] = useState<string | null>(null);
  const isViewerActive = useCallback(
    (instanceId: string) => {
      if (!optimizeEmbeds) return true;
      return activeInstanceId === instanceId;
    },
    [activeInstanceId, optimizeEmbeds],
  );

  return (
    <WorkspaceArtifactViewerContext.Provider
      value={{ activeInstanceId, optimizeEmbeds, isViewerActive, setActiveInstanceId }}
    >
      {children}
    </WorkspaceArtifactViewerContext.Provider>
  );
}

export function useWorkspaceArtifactViewer() {
  const context = useContext(WorkspaceArtifactViewerContext);
  if (!context) {
    throw new Error("useWorkspaceArtifactViewer must be used within a WorkspaceArtifactViewerProvider");
  }

  return context;
}
