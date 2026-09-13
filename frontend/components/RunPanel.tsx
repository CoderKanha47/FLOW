"use client";

import { useState } from "react";

import type { ExecutionDetail } from "@/lib/types";

interface RunPanelProps {
  onRun: (input: Record<string, unknown>) => Promise<void>;
  running: boolean;
  result: ExecutionDetail | null;
}

export default function RunPanel({ onRun, running, result }: RunPanelProps) {
  const [input, setInput] = useState("{\n  \n}");

  const handleRun = async () => {
    let parsed: Record<string, unknown> = {};
    const trimmed = input.trim();
    if (trimmed) {
      try {
        parsed = JSON.parse(trimmed);
        if (Array.isArray(parsed) || typeof parsed !== "object") {
          parsed = { data: parsed };
        }
      } catch {
        parsed = { raw: trimmed };
      }
    }
    await onRun(parsed);
  };

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Run workflow</h2>
      <div>
        <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate-400">
          Input (JSON)
        </label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={6}
          className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 font-mono text-xs text-slate-800 outline-none focus:border-cyan-500"
          spellCheck={false}
        />
        <p className="mt-1 text-[10px] text-slate-400">
          Reference values as <code className="text-cyan-600">{"{{input.key}}"}</code> or{" "}
          <code className="text-cyan-600">{"{{variables.key}}"}</code>. Add API keys as variables
          here, e.g. <code className="text-cyan-600">{"OPENAI_API_KEY"}</code>.
        </p>
      </div>

      <button
        onClick={handleRun}
        disabled={running}
        className="rounded-md bg-cyan-600 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {running ? "Running…" : "▶ Run"}
      </button>

      {result ? (
        <div className="rounded-md border border-slate-200 bg-white p-2">
          <div className="mb-1 flex items-center gap-2">
            <StatusBadge status={result.status} />
            <span className="text-[11px] text-slate-400">{result.duration_ms} ms</span>
          </div>
          <div className="max-h-48 overflow-auto">
            <pre className="whitespace-pre-wrap break-all font-mono text-[11px] leading-relaxed text-slate-600">
              {JSON.stringify(result.output ?? result.error, null, 2)}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    success: "bg-emerald-50 text-emerald-600 border-emerald-200",
    failed: "bg-rose-50 text-rose-600 border-rose-200",
    running: "bg-cyan-50 text-cyan-600 border-cyan-200",
    skipped: "bg-slate-50 text-slate-500 border-slate-200",
  };
  return (
    <span
      className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
        map[status] || map.skipped
      }`}
    >
      {status}
    </span>
  );
}