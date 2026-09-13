export interface NodeFieldMeta {
  key: string;
  label: string;
  type: string;
  options?: string[];
  placeholder?: string;
  help?: string;
  default?: unknown;
  secret?: boolean;
}

export interface NodeTypeMeta {
  type: string;
  label: string;
  category: string;
  description: string;
  icon: string;
  inputs: number;
  outputs: number;
  fields: NodeFieldMeta[];
}

export interface FlowPosition {
  x: number;
  y: number;
}

export interface FlowNode {
  id: string;
  type: string;
  name: string;
  position: FlowPosition;
  config: Record<string, unknown>;
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  branch?: string | null;
}

export interface Workflow {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  published: boolean;
  webhook_secret?: string;
  created_at?: string;
  updated_at?: string;
  nodes: FlowNode[];
  edges: FlowEdge[];
}

export interface ExecutionNodeDetail {
  id: string;
  node_id: string;
  node_type: string;
  status: "running" | "success" | "failed" | "skipped";
  input?: unknown;
  output?: unknown;
  error?: string | null;
  duration_ms?: number | null;
}

export interface ExecutionDetail {
  id: string;
  workflow_id: string;
  status: "running" | "success" | "failed";
  trigger: string;
  trigger_input?: unknown;
  output?: unknown;
  error?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  nodes: ExecutionNodeDetail[];
}

export interface ExecutionSummary {
  id: string;
  workflow_id: string;
  status: string;
  trigger: string;
  started_at?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  error?: string | null;
}