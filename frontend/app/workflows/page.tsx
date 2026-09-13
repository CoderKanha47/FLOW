"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, clearToken, currentUser } from "@/lib/api";
import type { Workflow } from "@/lib/types";

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<{ email: string } | null>(null);

  useEffect(() => {
    setUser(currentUser());
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setWorkflows(await api.listWorkflows());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const create = async () => {
    try {
      const wf = await api.createWorkflow({ name: "Untitled workflow", nodes: [], edges: [] });
      router.push(`/workflows/${wf.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const remove = async (id: string) => {
    try {
      await api.deleteWorkflow(id);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const logout = () => {
    clearToken();
    router.push("/login");
  };

  return (
    <div className="min-h-screen p-6 text-slate-800">
      <header className="mx-auto mb-8 flex max-w-4xl items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Flow</h1>
          <p className="text-xs text-slate-400">
            {user ? `Signed in as ${user.email}` : "Your workflows"}
          </p>
        </div>
        <button
          onClick={logout}
          className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50"
        >
          Sign out
        </button>
      </header>

      <main className="mx-auto max-w-4xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Workflows</h2>
          <button
            onClick={create}
            className="rounded-md bg-cyan-600 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-cyan-500"
          >
            + New workflow
          </button>
        </div>

        {error ? (
          <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-xs text-rose-600">{error}</div>
        ) : null}

        {loading ? (
          <div className="text-sm text-slate-400">Loading…</div>
        ) : workflows.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400">
            No workflows yet. Create one to start building.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {workflows.map((wf) => (
              <div
                key={wf.id}
                className="group flex flex-col rounded-lg border border-slate-200 bg-white p-4 transition-colors hover:border-slate-300 hover:shadow-sm"
              >
                <button onClick={() => router.push(`/workflows/${wf.id}`)} className="text-left">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-semibold">{wf.name}</span>
                    {wf.published ? (
                      <span className="shrink-0 rounded border border-emerald-200 bg-emerald-50 px-1.5 text-[10px] font-semibold uppercase text-emerald-600">
                        Live
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-400">
                    {wf.nodes.length} nodes · {wf.edges.length} connections
                  </div>
                </button>
                <div className="mt-3 flex items-center gap-2">
                  <button
                    onClick={() => router.push(`/workflows/${wf.id}`)}
                    className="rounded border border-slate-200 bg-white px-2 py-1 text-[11px] text-slate-600 hover:bg-slate-50"
                  >
                    Open
                  </button>
                  <button
                    onClick={() => remove(wf.id)}
                    className="rounded border border-rose-200 bg-white px-2 py-1 text-[11px] text-rose-500 hover:bg-rose-50"
                  >
                    Delete
                  </button>
                  {wf.published && (
                    <span className="ml-auto truncate font-mono text-[10px] text-slate-400">
                      hooks: /api/webhooks/{wf.id.slice(0, 8)}…
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-10 rounded-lg border border-slate-200 bg-white/60 p-4 text-[11px] leading-relaxed text-slate-400">
          <span className="font-semibold text-slate-500">Tip:</span> Design your workflow on the
          canvas, connect nodes, configure each node, then publish to expose a webhook endpoint.
          Trigger inputs are available as <code className="text-cyan-600">{"{{input.key}}"}</code>{" "}
          and previous node outputs as{" "}
          <code className="text-cyan-600">{"{{nodes.<node_id>.output.key}}"}</code>.
        </div>
      </main>
    </div>
  );
}