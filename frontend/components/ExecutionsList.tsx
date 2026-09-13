"use client";

import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/RunPanel";
import { api } from "@/lib/api";
import type { ExecutionDetail, ExecutionSummary } from "@/lib/types";

interface ExecutionsListProps {
  workflowId: string;
  onLoad: (execution: ExecutionDetail) => void;
  activeId?: string | null;
}

export default function ExecutionsList({ workflowId, onLoad, activeId }: ExecutionsListProps) {
  const [executions, setExecutions] = useState<ExecutionSummary[]>([]);

  useEffect(() => {
    api
      .listExecutions(workflowId)
      .then((list) => {
        setExecutions(list);
        if (list.length > 0) {
          api.getExecution(list[0].id).then(onLoad).catch(() => undefined);
        }
      })
      .catch(() => undefined);
  }, [workflowId, onLoad]);

  if (executions.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-xs text-slate-400">
        No executions yet. Run the workflow to see history.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-1 overflow-y-auto p-3">
      <h2 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">Executions</h2>
      {executions.map((e) => (
        <ExecutionRow key={e.id} e={e} active={e.id === activeId} onSelect={() => load(e.id)} />
      ))}
    </div>
  );

  async function load(id: string) {
    try {
      const detail = await api.getExecution(id);
      onLoad(detail);
    } catch {
      /* ignore */
    }
  }
}

function ExecutionRow({ e, active, onSelect }: { e: ExecutionSummary; active: boolean; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className={`flex items-center justify-between gap-2 rounded-md border px-2 py-1.5 text-left transition-colors ${
        active
          ? "border-cyan-500/50 bg-cyan-50"
          : "border-slate-200 bg-white hover:bg-slate-50"
      }`}
    >
      <div className="min-w-0">
        <div className="truncate font-mono text-[11px] text-slate-600">{e.id.slice(0, 14)}</div>
        <div className="text-[10px] text-slate-400">
          {e.trigger} · {e.duration_ms ?? "–"} ms
        </div>
      </div>
      <StatusBadge status={e.status} />
    </button>
  );
}