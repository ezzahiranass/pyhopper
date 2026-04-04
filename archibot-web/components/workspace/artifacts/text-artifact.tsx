import type { WorkspaceTextArtifact } from "@/components/studio/types";

export function WorkspaceTextArtifactView({
  artifact,
}: {
  artifact: WorkspaceTextArtifact;
}) {
  return (
    <section className="workspace-artifact">
      <span className="workspace-artifact__label">{artifact.label}</span>
      <p className="workspace-artifact__text">{artifact.value}</p>
    </section>
  );
}
