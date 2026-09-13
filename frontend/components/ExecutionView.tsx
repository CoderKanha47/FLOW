"use client";

import { useState } from "react";

import { StatusBadge } from "@/components/RunPanel";
import type { ExecutionDetail, ExecutionNodeDetail } from "@/lib/types";

interface ExecutionViewProps {
  execution: ExecutionDetail;
}

export default function ExecutionView({ execution }: ExecutionViewProps) {
  const [opened, setOpened] = useState<string | null>(null);

  return (
    <div className="flex h-full flex-col overflow-y-auto p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700">Execution {execution.id.slice(0, 8)}</span>
          <StatusBadge status={execution.status} />
        </div>
        <span className="text-[11px] text-slate-400">{execution.duration_ms} ms</span>
      </div>

      {execution.error ? (
        <div className="mb-2 rounded-md border border-rose-200 bg-rose-50 p-2 text-xs text-rose-600">
          {execution.error}
        </div>
      ) : null}

      <div className="mb-2 rounded-md border border-slate-200 bg-white p-2">
        <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
          Final output
        </div>
        <pre className="whitespace-pre-wrap break-all font-mono text-[11px] text-slate-600">
          {JSON.stringify(execution.output ?? null, null, 2)}
        </pre>
      </div>

      <div className="flex flex-col gap-1">
        {execution.nodes.map((n) => (
          <NodeRow key={n.id} node={n} open={opened === n.node_id} onToggle={() => setOpened(opened === n.node_id ? null : n.node_id)} />
        ))}
      </div>
    </div>
  );
}

function NodeRow({
  node,
  open,
  onToggle,
}: {
  node: ExecutionNodeDetail;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-white">
      <button onClick={onToggle} className="flex w-full items-center gap-2 px-2 py-1.5 text-left">
        <span className="text-[10px] text-slate-400">{node.duration_ms ?? "–"} ms</span>
        <span className="min-w-0 flex-1 truncate text-xs font-medium text-slate-700">{node.node_id}</span>
        <StatusBadge status={node.status} />
      </button>
      {open ? (
        <div className="border-t border-slate-100 p-2">
          {node.error ? (
            <div className="mb-2 rounded bg-rose-50 p-1.5 text-[11px] text-rose-600">{node.error}</div>
          ) : null}
          <Detail title="Output" value={node.output} />
          <Detail title="Input" value={node.input} />
        </div>
      ) : null}
    </div>
  );
}

function Detail({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="mb-2">
      <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">{title}</div>
      <pre className="max-h-32 whitespace-pre-wrap break-all rounded bg-slate-100 p-1.5 font-mono text-[10px] leading-relaxed text-slate-600">
        {JSON.stringify(value ?? null, null, 2)}
      </pre>
    </div>
  );
}