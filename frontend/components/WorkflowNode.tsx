"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { memo } from "react";

import type { RFNode } from "@/lib/flow";
import { useNodeMeta } from "@/lib/nodeMetaContext";
import { nodeVisual } from "@/lib/nodeVisuals";

function WorkflowNodeInner({ data, selected }: NodeProps<RFNode>) {
  const meta = useNodeMeta().get(data.wfType);
  const visual = nodeVisual(data.wfType);
  const Icon = visual.icon;
  const title = data.name || meta?.label || data.label;
  const subtitle = data.name && data.name !== meta?.label ? meta?.label : undefined;

  return (
    <div
      className={`w-[164px] rounded-[10px] border bg-white shadow-[0_1px_3px_rgba(15,23,42,0.08),0_4px_12px_rgba(15,23,42,0.06)] transition-shadow ${
        selected ? "ring-2 shadow-md" : "hover:shadow-md"
      }`}
      style={{ borderColor: selected ? "#0ea5e9" : "#e2e6eb" }}
    >
      <Handle type="target" position={Position.Left} className="!h-2.5 !w-2.5 !border !border-white !bg-gray-300" />
      <div className="flex items-center gap-2 px-3 pt-2.5 pb-1.5">
        <span
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md"
          style={{ backgroundColor: visual.color }}
        >
          <Icon className="h-4 w-4 text-white" strokeWidth={2.2} />
        </span>
        <div className="min-w-0">
          <div className="truncate text-xs font-semibold text-slate-800">{title}</div>
          {subtitle ? <div className="truncate text-[10px] text-slate-400">{subtitle}</div> : null}
        </div>
      </div>
      {meta?.description ? (
        <div className="line-clamp-2 px-3 pb-1 text-[10px] leading-snug text-slate-500">{meta.description}</div>
      ) : null}
      <div className="flex items-center gap-1 px-3 pb-2">
        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-slate-500">
          {data.status || "Unassigned"}
        </span>
      </div>
      <Handle type="source" position={Position.Right} className="!h-2.5 !w-2.5 !border !border-white !bg-gray-300" />
    </div>
  );
}

export default memo(WorkflowNodeInner);