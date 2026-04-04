"use client";

import { useEffect, useRef, useState } from "react";
import { Box } from "lucide-react";
import { getBlob, ref } from "firebase/storage";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { WorkspaceModelArtifact } from "@/components/studio/types";
import { useWorkspaceArtifactViewer } from "@/components/workspace/artifacts/artifact-viewer-context";
import { storage } from "@/lib/firebase";

function buildArtifactInstanceId(subdomainId: string, artifactId: string) {
  return `${subdomainId}:${artifactId}`;
}

function fitCameraToObject(camera: THREE.PerspectiveCamera, object: THREE.Object3D) {
  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDimension = Math.max(size.x, size.y, size.z) || 1;
  const distance = maxDimension / (2 * Math.tan((camera.fov * Math.PI) / 360));

  camera.position.set(center.x + distance * 1.15, center.y + distance * 0.75, center.z + distance * 1.15);
  camera.near = Math.max(distance / 100, 0.01);
  camera.far = distance * 100;
  camera.lookAt(center);
  camera.updateProjectionMatrix();
  return center;
}

export function WorkspaceModelArtifactView({
  artifactId,
  subdomainId,
  artifact,
}: {
  artifactId: string;
  subdomainId: string;
  artifact: WorkspaceModelArtifact;
}) {
  const instanceId = buildArtifactInstanceId(subdomainId, artifactId);
  const { isViewerActive, setActiveInstanceId } = useWorkspaceArtifactViewer();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const frameRef = useRef<number | null>(null);
  const modelRootRef = useRef<THREE.Object3D | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [modelBuffer, setModelBuffer] = useState<ArrayBuffer | null>(null);
  const isActive = isViewerActive(instanceId);

  useEffect(() => {
    let cancelled = false;

    async function resolveModelBuffer() {
      if (artifact.value.storagePath) {
        try {
          const storageRef = ref(storage, artifact.value.storagePath);
          const blob = await getBlob(storageRef);
          if (!cancelled) {
            setModelBuffer(await blob.arrayBuffer());
            setLoadError(null);
          }
          return;
        } catch (error) {
          console.error("Failed to resolve Firebase Storage blob for model artifact", error);
        }
      }

      if (!artifact.value.url) {
        if (!cancelled) {
          setModelBuffer(null);
        }
        return;
      }

      try {
        const response = await fetch(artifact.value.url, { mode: "cors" });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        if (!cancelled) {
          setModelBuffer(await response.arrayBuffer());
          setLoadError(null);
        }
      } catch (error) {
        console.error("Failed to fetch workspace model artifact bytes", error);
        if (!cancelled) {
          setModelBuffer(null);
          setLoadError("Model bytes could not be loaded.");
        }
      }
    }

    void resolveModelBuffer();

    return () => {
      cancelled = true;
    };
  }, [artifact.value.storagePath, artifact.value.url]);

  useEffect(() => {
    if (!isActive || !containerRef.current || rendererRef.current || !modelBuffer) return;

    const container = containerRef.current;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#e2e8f0");
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 1000);
    camera.position.set(2.4, 1.8, 2.4);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    rendererRef.current = renderer;
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(0, 0, 0);
    controlsRef.current = controls;

    scene.add(new THREE.HemisphereLight("#ffffff", "#94a3b8", 1.35));
    const keyLight = new THREE.DirectionalLight("#ffffff", 1.15);
    keyLight.position.set(3, 4, 2);
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight("#bfdbfe", 0.7);
    fillLight.position.set(-2, 1.5, -3);
    scene.add(fillLight);

    const grid = new THREE.GridHelper(6, 6, "#94a3b8", "#cbd5e1");
    grid.position.y = -0.75;
    scene.add(grid);

    const loader = new GLTFLoader();
    loader.parse(
      modelBuffer,
      "",
      (gltf) => {
        setLoadError(null);
        const root = gltf.scene;
        root.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.castShadow = false;
            child.receiveShadow = false;
            if (child.geometry && !child.geometry.getAttribute("normal")) {
              child.geometry.computeVertexNormals();
            }
          }
        });
        modelRootRef.current = root;
        scene.add(root);
        const center = fitCameraToObject(camera, root);
        controls.target.copy(center);
        controls.update();
      },
      (error) => {
        console.error("Failed to load workspace model artifact", error);
        setLoadError("Model preview failed to load.");
      },
    );

    const resize = () => {
      const width = container.clientWidth;
      const height = container.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    const observer = new ResizeObserver(() => resize());
    observer.observe(container);
    resize();

    const renderFrame = () => {
      frameRef.current = window.requestAnimationFrame(renderFrame);
      controls.update();
      renderer.render(scene, camera);
    };
    renderFrame();

    return () => {
      observer.disconnect();
      if (frameRef.current != null) {
        window.cancelAnimationFrame(frameRef.current);
      }
      controls.dispose();
      renderer.dispose();
      if (modelRootRef.current) {
        scene.remove(modelRootRef.current);
        modelRootRef.current = null;
      }
      container.innerHTML = "";
      controlsRef.current = null;
      rendererRef.current = null;
      cameraRef.current = null;
      sceneRef.current = null;
    };
  }, [isActive, modelBuffer]);

  return (
    <section className={`workspace-artifact workspace-artifact--model${isActive ? " is-active" : ""}`}>
      <span className="workspace-artifact__label">{artifact.label}</span>
      {isActive ? (
        <div
          className="workspace-artifact__model-preview workspace-artifact__model-preview--active workspace-artifact__interactive"
          onPointerDown={(event) => event.stopPropagation()}
        >
          <div ref={containerRef} className="workspace-artifact__model-canvas" />
          {loadError ? <span className="workspace-artifact__model-error">{loadError}</span> : null}
        </div>
      ) : (
        <button
          type="button"
          className="workspace-artifact__model-toggle workspace-artifact__interactive"
          onClick={() => setActiveInstanceId(instanceId)}
          onPointerDown={(event) => event.stopPropagation()}
        >
          <div className="workspace-artifact__model-preview">
            <div className="workspace-artifact__model-icon-shell" aria-hidden="true">
              <span className="workspace-artifact__model-icon">
                <Box size={18} />
              </span>
            </div>
            <span className="workspace-artifact__model-action">
              Open 3D preview
            </span>
            <span className="sr-only">
              {`Open ${artifact.label} ${artifact.value.format ?? "model"} preview`}
            </span>
          </div>
        </button>
      )}
    </section>
  );
}
