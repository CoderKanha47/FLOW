import { MarkerType, type Edge, type Node } from "@xyflow/react";

import type {
  FlowEdge,
  FlowNode,
  FlowPosition,
} from "./types";

export interface RFNodeData {
  wfType: string;
  label: string;
  icon: string;
  category: string;
  name: string;
  config: Record<string, unknown>;
  status?: string;
  description?: string;
  [key: string]: unknown;
}

export type RFNode = Node<RFNodeData>;
export type RFEdge = Edge & { branch?: string | null };

const CATEGORY_COLORS: Record<string, string> = {
  Trigger: "#3b82f6",
  Logic: "#f59e0b",
  Integration: "#10b981",
  AI: "#8b5cf6",
  Utility: "#64748b",
};

const EDGE_COLOR = "#b6bcc4";
const BRANCH_COLOR = "#f59e0b";

export function makeEdgeMarker(branch: string | null | undefined) {
  return {
    type: MarkerType.ArrowClosed,
    width: 14,
    height: 14,
    color: branch ? BRANCH_COLOR : EDGE_COLOR,
  };
}

export function makeEdgeStyle(branch: string | null | undefined): Edge["style"] {
  return {
    stroke: branch ? BRANCH_COLOR : EDGE_COLOR,
    strokeWidth: 1.5,
    strokeDasharray: "6 6",
  };
}

export function categoryColor(category: string): string {
  return CATEGORY_COLORS[category] || "#64748b";
}

export function toRFNodes(nodes: FlowNode[]): RFNode[] {
  return nodes.map((n) => ({
    id: n.id,
    type: "workflow",
    position: { x: n.position.x, y: n.position.y },
    data: {
      wfType: n.type,
      label: n.type,
      icon: "⚙️",
      category: "Utility",
      name: n.name || "",
      config: n.config,
    },
  }));
}

export function createNodeData(type: string, label: string): RFNode["data"] {
  return {
    wfType: type,
    label,
    icon: "⚙️",
    category: "Utility",
    name: label,
    config: {},
  };
}

export function toRFEdges(edges: FlowEdge[]): RFEdge[] {
  return edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: "default",
    branch: e.branch ?? null,
    label: e.branch ?? undefined,
    style: makeEdgeStyle(e.branch),
    markerEnd: makeEdgeMarker(e.branch),
    labelStyle: { fill: BRANCH_COLOR, fontSize: 11, fontWeight: 600 },
  }));
}

export function fromRFNodes(nodes: RFNode[]): FlowNode[] {
  return nodes.map((n) => ({
    id: n.id,
    type: n.data.wfType,
    name: n.data.name || "",
    position: { x: n.position.x, y: n.position.y } as FlowPosition,
    config: n.data.config || {},
  }));
}

export function fromRFEdges(edges: RFEdge[]): FlowEdge[] {
  return edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    branch: e.branch ?? null,
  }));
}

export function genId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36).slice(-4)}`;
}