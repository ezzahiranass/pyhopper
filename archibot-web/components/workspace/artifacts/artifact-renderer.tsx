import type { WorkspaceArtifact } from "@/components/studio/types";
import { WorkspaceGeolocationArtifactView } from "@/components/workspace/artifacts/geolocation-artifact";
import { WorkspaceImageArtifactView } from "@/components/workspace/artifacts/image-artifact";
import { WorkspaceModelArtifactView } from "@/components/workspace/artifacts/model-artifact";
import { WorkspaceTextArtifactView } from "@/components/workspace/artifacts/text-artifact";

export function WorkspaceArtifactRenderer({
  artifactId,
  subdomainId,
  artifact,
}: {
  artifactId: string;
  subdomainId: string;
  artifact: WorkspaceArtifact;
}) {
  if (artifact.type === "text") {
    return <WorkspaceTextArtifactView artifact={artifact} />;
  }

  if (artifact.type === "geolocation") {
    return (
      <WorkspaceGeolocationArtifactView
        artifactId={artifactId}
        subdomainId={subdomainId}
        artifact={artifact}
      />
    );
  }

  if (artifact.type === "image") {
    return <WorkspaceImageArtifactView artifact={artifact} />;
  }

  if (artifact.type === "model") {
    return (
      <WorkspaceModelArtifactView
        artifactId={artifactId}
        subdomainId={subdomainId}
        artifact={artifact}
      />
    );
  }

  return null;
}
