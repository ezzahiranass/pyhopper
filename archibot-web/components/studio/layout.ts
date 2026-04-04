import type { Edge, Node } from "@xyflow/react";
import { Position } from "@xyflow/react";
import { OrgChartItem, OrgChartNodeData, PersonalityOption } from "@/components/studio/types";

const NODE_WIDTH = 260;
const NODE_HEIGHT = 152;
const EDITING_NODE_WIDTH = 280;
const EDITING_NODE_HEIGHT = 324;
const HORIZONTAL_GAP = 52;
const VERTICAL_GAP = 120;

type NodeActions = {
  personalities: PersonalityOption[];
  onSelect: (id: string) => void;
  onStartEdit: (id: string) => void;
  onStopEdit: () => void;
  onAddChild: (parentId: string) => void;
  onDelete: (id: string) => void;
  onSubmitEdit: (
    id: string,
    value: {
      name: string;
      job: OrgChartItem["job"];
      description: string;
      personality: string;
    },
  ) => void;
};

export function buildFlowChart(
  items: OrgChartItem[],
  selectedId: string,
  personalities: PersonalityOption[],
  onSelect: NodeActions["onSelect"],
  editingId: string | null,
  onStartEdit: NodeActions["onStartEdit"],
  onStopEdit: NodeActions["onStopEdit"],
  onAddChild: NodeActions["onAddChild"],
  onDelete: NodeActions["onDelete"],
  onSubmitEdit: NodeActions["onSubmitEdit"],
): { nodes: Node<OrgChartNodeData>[]; edges: Edge[] } {
  const childrenMap = new Map<string | null, OrgChartItem[]>();

  for (const item of items) {
    const siblings = childrenMap.get(item.parentId) ?? [];
    siblings.push(item);
    childrenMap.set(item.parentId, siblings);
  }

  const roots = childrenMap.get(null) ?? [];
  let cursor = 0;
  const positions = new Map<string, { x: number; y: number }>();

  const placeNode = (item: OrgChartItem, depth: number): number => {
    const children = childrenMap.get(item.id) ?? [];
    const childCenters = children.map((child) => placeNode(child, depth + 1));

    const center =
      childCenters.length > 0
        ? childCenters.reduce((sum, value) => sum + value, 0) / childCenters.length
        : cursor++ * (NODE_WIDTH + HORIZONTAL_GAP);

    positions.set(item.id, {
      x: center,
      y: depth * (NODE_HEIGHT + VERTICAL_GAP),
    });

    return center;
  };

  for (const root of roots) {
    placeNode(root, 0);
    cursor += 1;
  }

  const allPositions = Array.from(positions.values());
  const minX = Math.min(...allPositions.map((p) => p.x), 0);
  const horizontalOffset = minX < 0 ? Math.abs(minX) + HORIZONTAL_GAP : HORIZONTAL_GAP;

  const nodes: Node<OrgChartNodeData>[] = items.map((item) => {
    const position = positions.get(item.id) ?? { x: 0, y: 0 };
    const isEditing = item.id === editingId;
    const width = isEditing ? EDITING_NODE_WIDTH : NODE_WIDTH;
    const height = isEditing ? EDITING_NODE_HEIGHT : NODE_HEIGHT;

    return {
      id: item.id,
      type: "orgChart",
      selected: item.id === selectedId,
      position: {
        x: position.x + horizontalOffset + (NODE_WIDTH - width) / 2,
        y: position.y + VERTICAL_GAP / 2 + (NODE_HEIGHT - height) / 2,
      },
      draggable: false,
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
      data: {
        name: item.name,
        job: item.job,
        description: item.description,
        personality: item.personality,
        personalities,
        isRoot: item.parentId === null,
        isEditing,
        onSelect: () => onSelect(item.id),
        onStartEdit: () => onStartEdit(item.id),
        onStopEdit,
        onAddChild: () => onAddChild(item.id),
        onDelete: () => onDelete(item.id),
        onSubmitEdit: (value) => onSubmitEdit(item.id, value),
      },
    };
  });

  const edges: Edge[] = items
    .filter((item) => item.parentId)
    .map((item) => ({
      id: `${item.parentId}-${item.id}`,
      source: item.parentId!,
      target: item.id,
      type: "smoothstep",
      animated: false,
      selectable: false,
    }));

  return { nodes, edges };
}
