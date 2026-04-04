import type { WorkspaceImageArtifact } from "@/components/studio/types";

export function WorkspaceImageArtifactView({
  artifact,
}: {
  artifact: WorkspaceImageArtifact;
}) {
  return (
    <section className="workspace-artifact">
      <span className="workspace-artifact__label">{artifact.label}</span>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className="workspace-artifact__image"
        src={artifact.value.url}
        alt={artifact.value.alt ?? artifact.label}
      />
    </section>
  );
}
