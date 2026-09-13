"use client";

import { Background, BackgroundVariant, MiniMap, ReactFlow, useReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback } from "react";

import WorkflowNode from "@/components/WorkflowNode";
import { categoryColor, createNodeData, type RFEdge, type RFNode } from "@/lib/flow";
import { NodeMetaContext } from "@/lib/nodeMetaContext";
import { nodeVisual } from "@/lib/nodeVisuals";
import type { NodeTypeMeta } from "@/lib/types";

const nodeTypes = { workflow: WorkflowNode };

interface FlowCanvasProps {
  nodes: RFNode[];
  edges: RFEdge[];
  meta: Map<string, NodeTypeMeta>;
  locked?: boolean;
  dark?: boolean;
  onNodesChange: (changes: unknown) => void;
  onEdgesChange: (changes: unknown) => void;
  onConnect: (connection: unknown) => void;
  onAddNode: (node: RFNode) => void;
  onSelect: (id: string | null) => void;
}

export default function FlowCanvas({
  nodes,
  edges,
  meta,
  locked = false,
  dark = false,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onAddNode,
  onSelect,
}: FlowCanvasProps) {
  const { screenToFlowPosition } = useReactFlow();

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData("application/flow-node");
      if (!type) return;
      const m = meta.get(type);
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      onAddNode({
        id: `${type}_${Date.now().toString(36)}`,
        type: "workflow",
        position: { x: position.x - 82, y: position.y - 26 },
        width: 164,
        data: createNodeData(type, m?.label || type),
      } as RFNode);
    },
    [meta, screenToFlowPosition, onAddNode]
  );

  return (
    <NodeMetaContext.Provider value={meta}>
      <div
        className={`h-full w-full ${dark ? "bg-slate-900" : "bg-transparent"}`}
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = "move";
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) => onSelect(node.id)}
          onPaneClick={() => onSelect(null)}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.2}
          maxZoom={2}
          nodesDraggable={!locked}
          elementsSelectable={!locked}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={22} size={1.5} color={dark ? "#475569" : "#d8dbe0"} />
          <MiniMap
            pannable
            zoomable
            position="bottom-right"
            className={`!rounded-lg !border !shadow-sm ${
              dark
                ? "!border-slate-700 !bg-slate-800/90"
                : "!border-slate-200 !bg-white/90"
            }`}
            maskColor={dark ? "rgba(15,23,42,0.7)" : "rgba(243,244,246,0.7)"}
            nodeStrokeWidth={0}
            nodeColor={(n) => {
              const t = String((n.data as { wfType?: string })?.wfType ?? "");
              return nodeVisual(t).color || categoryColor("Utility");
            }}
          />
        </ReactFlow>
      </div>
    </NodeMetaContext.Provider>
  );
}