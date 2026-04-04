"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import { buildFlowChart } from "@/components/studio/layout";
import { createAgentJob, createAgentName, getJobDescription } from "@/components/studio/data";
import { useStudio } from "@/components/studio/studio-context";
import OrgChartNode from "@/components/studio/org-chart-node";
import { OrgChartItem } from "@/components/studio/types";

const nodeTypes = { orgChart: OrgChartNode } as const;

function createNodeId() {
  return crypto.randomUUID();
}

type Props = {
  items: OrgChartItem[];
  onItemsChange: (items: OrgChartItem[]) => void;
  onSelectionChange: (item: OrgChartItem | null) => void;
};

function OrgChartEditorInner({ items, onItemsChange, onSelectionChange }: Props) {
  const { jobs, personalities } = useStudio();
  const reactFlow = useReactFlow();
  const [selectedId, setSelectedId] = useState<string>(items[0]?.id ?? "");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newNodeCount, setNewNodeCount] = useState(1);

  const handleSelect = useCallback((id: string) => {
    setSelectedId(id);
    const found = items.find((item) => item.id === id) ?? null;
    onSelectionChange(found);
  }, [items, onSelectionChange]);

  const focusNode = useCallback((id: string) => {
    requestAnimationFrame(() => {
      const node = reactFlow.getNode(id);
      if (!node) return;

      const width = node.measured?.width ?? (editingId === id ? 280 : 260);
      const height = node.measured?.height ?? (editingId === id ? 324 : 152);

      reactFlow.setCenter(
        node.position.x + width / 2,
        node.position.y + height / 2,
        { zoom: 0.95, duration: 260 },
      );
    });
  }, [editingId, reactFlow]);

  const handleStartEdit = useCallback((id: string) => {
    setEditingId(id);
    setSelectedId(id);
    const found = items.find((item) => item.id === id) ?? null;
    onSelectionChange(found);
    focusNode(id);
  }, [focusNode, items, onSelectionChange]);

  const handleStopEdit = useCallback(() => {
    setEditingId(null);
  }, []);

  const handleAddChild = useCallback((parentId?: string) => {
    const effectiveParentId = parentId ?? selectedId ?? items[0]?.id ?? null;
    if (!effectiveParentId) return;

    const newId = createNodeId();
    const job = createAgentJob(newNodeCount, jobs);
    const newItem: OrgChartItem = {
      id: newId,
      parentId: effectiveParentId,
      name: createAgentName(newNodeCount),
      job,
      description: getJobDescription(job, jobs),
      personality: "",
    };

    const next = [...items, newItem];
    onItemsChange(next);
    setSelectedId(newId);
    onSelectionChange(newItem);
    setNewNodeCount((count) => count + 1);
  }, [items, jobs, newNodeCount, onItemsChange, onSelectionChange, selectedId]);

  useEffect(() => {
    if (!editingId) return;
    focusNode(editingId);
  }, [editingId, focusNode, items]);

  const handleDelete = useCallback((id: string) => {
    const idsToDelete = new Set<string>([id]);
    let changed = true;
    while (changed) {
      changed = false;
      for (const item of items) {
        if (item.parentId && idsToDelete.has(item.parentId) && !idsToDelete.has(item.id)) {
          idsToDelete.add(item.id);
          changed = true;
        }
      }
    }

    const next = items.filter((item) => !idsToDelete.has(item.id));
    const fallback = next.find((item) => item.parentId === null)?.id ?? next[0]?.id ?? "";
    const nextSelectedId = idsToDelete.has(selectedId) ? fallback : selectedId;

    onItemsChange(next);
    setSelectedId(nextSelectedId);
    if (editingId && idsToDelete.has(editingId)) {
      setEditingId(null);
    }
    onSelectionChange(next.find((item) => item.id === nextSelectedId) ?? null);
  }, [editingId, items, onItemsChange, onSelectionChange, selectedId]);

  const handleSubmitEdit = useCallback((id: string, value: {
    name: string;
    job: OrgChartItem["job"];
    description: string;
    personality: string;
  }) => {
    const next = items.map((item) => (
      item.id === id
        ? {
            ...item,
            name: value.name,
            job: value.job,
            description: value.description,
            personality: value.personality,
          }
        : item
    ));
    onItemsChange(next);
    if (id === selectedId) {
      onSelectionChange(next.find((item) => item.id === id) ?? null);
    }
  }, [items, onItemsChange, onSelectionChange, selectedId]);

  const flowData = useMemo(
    () => buildFlowChart(
      items,
      selectedId,
      personalities,
      handleSelect,
      editingId,
      handleStartEdit,
      handleStopEdit,
      handleAddChild,
      handleDelete,
      handleSubmitEdit,
    ),
    [
      editingId,
      handleAddChild,
      handleDelete,
      handleSubmitEdit,
      handleSelect,
      handleStartEdit,
      handleStopEdit,
      items,
      personalities,
      selectedId,
    ],
  );

  return (
    <div className="studio-canvas-fullpage">
      <ReactFlow
        fitView
        nodes={flowData.nodes}
        edges={flowData.edges}
        nodeTypes={nodeTypes as never}
        minZoom={0.2}
        maxZoom={1.5}
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        onNodeClick={(_, node) => handleSelect(node.id)}
      >
        <Background color="var(--studio-grid)" gap={24} size={1} />
        <MiniMap
          pannable
          zoomable
          nodeColor={() => "var(--studio-minimap-node)"}
          maskColor="rgb(240 240 240 / 0.72)"
          className="studio-minimap"
        />
        <Controls className="studio-controls" showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

export function OrgChartEditor(props: Props) {
  return (
    <ReactFlowProvider>
      <OrgChartEditorInner {...props} />
    </ReactFlowProvider>
  );
}
