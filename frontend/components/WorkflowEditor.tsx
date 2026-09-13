"use client";

import {
  ReactFlowProvider,
  addEdge as rfAddEdge,
  applyEdgeChanges,
  applyNodeChanges,
} from "@xyflow/react";
import { PanelRightClose } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import AppNav from "@/components/AppNav";
import CanvasChrome from "@/components/CanvasChrome";
import ExecutionsList from "@/components/ExecutionsList";
import ExecutionView from "@/components/ExecutionView";
import FlowCanvas from "@/components/FlowCanvas";
import NodeConfigPanel from "@/components/NodeConfigPanel";
import RunPanel from "@/components/RunPanel";
import { api } from "@/lib/api";
import { fromRFEdges, fromRFNodes, makeEdgeMarker, makeEdgeStyle, toRFEdges, toRFNodes, type RFEdge, type RFNode } from "@/lib/flow";
import type { ExecutionDetail, NodeTypeMeta, Workflow } from "@/lib/types";

interface WorkflowEditorProps {
  workflowId: string;
}

export default function WorkflowEditor({ workflowId }: WorkflowEditorProps) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [metaList, setMetaList] = useState<NodeTypeMeta[]>([]);
  const [nodes, setNodes] = useState<RFNode[]>([]);
  const [edges, setEdges] = useState<RFEdge[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tab, setTab] = useState<"run" | "history">("run");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ExecutionDetail | null>(null);
  const [activeExecution, setActiveExecution] = useState<ExecutionDetail | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [locked, setLocked] = useState(false);
  const [dark, setDark] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const loadedRef = useRef(false);

  const metaMap = useMemo(() => {
    const m = new Map<string, NodeTypeMeta>();
    for (const nm of metaList) m.set(nm.type, nm);
    return m;
  }, [metaList]);

  useEffect(() => {
    api.nodeTypes().then(setMetaList).catch(showError);
  }, []);

  useEffect(() => {
    loadedRef.current = false;
    api
      .getWorkflow(workflowId)
      .then((wf) => {
        setWorkflow(wf);
        setNodes(toRFNodes(wf.nodes));
        setEdges(toRFEdges(wf.edges));
        setSelectedId(null);
        setResult(null);
        setActiveExecution(null);
        setSaveState("idle");
        loadedRef.current = true;
      })
      .catch(showError);
  }, [workflowId]);

  const onNodesChange = useCallback((changes: unknown) => {
    setNodes((nds) => applyNodeChanges(changes as never, nds as never) as unknown as RFNode[]);
  }, []);
  const onEdgesChange = useCallback((changes: unknown) => {
    setEdges((eds) => applyEdgeChanges(changes as never, eds as never) as unknown as RFEdge[]);
  }, []);

  const onConnect = useCallback((connection: unknown) => {
    setEdges((eds) =>
      rfAddEdge(
        {
          ...(connection as object),
          type: "default",
          branch: null,
          style: makeEdgeStyle(null),
          markerEnd: makeEdgeMarker(null),
          labelStyle: { fill: "#f59e0b", fontSize: 11, fontWeight: 600 },
        } as never,
        eds
      )
    );
  }, []);

  const onAddNode = useCallback((node: RFNode) => {
    setNodes((nds) => [...nds, node]);
    setSelectedId(node.id);
  }, []);

  const onUpdateNode = useCallback(
    (id: string, patch: { name?: string; config?: Record<string, unknown> }) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === id
            ? {
                ...n,
                data: {
                  ...n.data,
                  name: patch.name ?? n.data.name,
                  config: patch.config ?? n.data.config,
                },
              }
            : n
        )
      );
    },
    []
  );

  const onBranch = useCallback((edgeId: string, branch: string) => {
    setEdges((eds) =>
      eds.map((e) =>
        e.id === edgeId
          ? {
              ...e,
              branch: branch || null,
              label: branch || undefined,
              style: makeEdgeStyle(branch || null),
              markerEnd: makeEdgeMarker(branch || null),
            }
          : e
      )
    );
  }, []);

  // Autosave when the graph or workflow meta changes and the workflow is loaded.
  useEffect(() => {
    if (!workflow || !loadedRef.current) return;
    const t = setTimeout(() => persistWorkflow("saving"), 900);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, workflow?.name, workflow?.published]);

  async function persistWorkflow(state: "idle" | "saving" | "saved") {
    if (!workflow) return;
    setSaveState(state);
    try {
      const updated = await api.updateWorkflow(workflow.id, {
        name: workflow.name,
        description: workflow.description,
        published: workflow.published,
        nodes: fromRFNodes(nodes),
        edges: fromRFEdges(edges),
      });
      setWorkflow((wf) => (wf ? { ...wf, ...updated } : wf));
      setSaveState("saved");
    } catch (e) {
      setSaveState("error");
      showError(e);
    }
  }

  const handleRun = useCallback(
    async (input: Record<string, unknown>) => {
      if (!workflow) return;
      setRunning(true);
      try {
        const exec = await api.runWorkflow(workflow.id, input);
        setResult(exec);
        setActiveExecution(exec);
        setTab("history");
      } catch (e) {
        showError(e);
      } finally {
        setRunning(false);
      }
    },
    [workflow]
  );

  function showError(e: unknown) {
    setError(e instanceof Error ? e.message : String(e));
  }

  const selectedNode = nodes.find((n) => n.id === selectedId) ?? null;

  return (
    <ReactFlowProvider>
      <div className={`relative flex h-screen overflow-hidden text-slate-800 ${dark ? "bg-slate-900" : "bg-[#f6f7f9]"}`}>
        <AppNav />

        {error ? (
          <div className="absolute top-0 right-0 left-[52px] z-30 flex items-center justify-between border-b border-rose-200 bg-rose-50 px-4 py-1.5 text-xs text-rose-600">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-600">
              ✕
            </button>
          </div>
        ) : null}

        <div className="flex min-h-0 flex-1">
          {/* Center: canvas + floating chrome */}
          <div id="flow-canvas" className="relative min-w-0 flex-1">
            <FlowCanvas
              nodes={nodes}
              edges={edges}
              meta={metaMap}
              locked={locked}
              dark={dark}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onAddNode={onAddNode}
              onSelect={setSelectedId}
            />
            <CanvasChrome
              meta={metaList}
              locked={locked}
              dark={dark}
              collapsed={collapsed}
              onAddNode={onAddNode}
              onToggleLock={() => setLocked((v) => !v)}
              onToggleDark={() => setDark((v) => !v)}
              onToggleInspector={() => setCollapsed((v) => !v)}
            />
          </div>

          {/* Right: collapsible inspector */}
          {!collapsed ? (
            <aside className="flex w-80 shrink-0 flex-col border-l border-slate-200 bg-white">
              <div className="flex flex-col gap-1.5 border-b border-slate-200 px-3 py-2">
                <div className="flex items-center gap-2">
                  <input
                    value={workflow?.name ?? "Loading…"}
                    onChange={(e) => setWorkflow((wf) => (wf ? { ...wf, name: e.target.value } : wf))}
                    className="min-w-0 flex-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-sm font-medium text-slate-800 outline-none focus:border-cyan-500"
                  />
                  <button
                    title="Collapse inspector"
                    onClick={() => setCollapsed(true)}
                    className="flex h-7 w-7 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
                  >
                    <PanelRightClose className="h-4 w-4" />
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  {saveState === "saving" && <span className="text-[11px] text-slate-400">Saving…</span>}
                  {saveState === "saved" && <span className="text-[11px] text-emerald-600">Saved</span>}
                  {saveState === "error" && <span className="text-[11px] text-rose-500">Save failed</span>}
                  <button
                    onClick={() => persistWorkflow("saving")}
                    className="rounded border border-slate-300 bg-white px-2 py-0.5 text-[11px] font-medium text-slate-600 hover:bg-slate-100"
                  >
                    Save
                  </button>
                  <span className="flex-1" />
                  <label className="flex cursor-pointer items-center gap-1.5 text-[11px] text-slate-500">
                    <input
                      type="checkbox"
                      className="h-3.5 w-3.5 accent-cyan-500"
                      checked={workflow?.published ?? false}
                      onChange={(e) => setWorkflow((wf) => (wf ? { ...wf, published: e.target.checked } : wf))}
                    />
                    Published
                  </label>
                </div>
              </div>

              <div className="flex border-b border-slate-200">
                {(
                  [
                    ["run", "Run"],
                    ["history", "History"],
                  ] as const
                ).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setTab(key)}
                    className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                      tab === key ? "border-b-2 border-cyan-500 text-cyan-600" : "text-slate-400 hover:text-slate-600"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {selectedNode ? (
                <div className="flex-1 overflow-hidden">
                  <div className="flex items-center justify-between border-b border-slate-200 px-3 py-1.5">
                    <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Node config</span>
                    <button
                      onClick={() => setSelectedId(null)}
                      className="text-[11px] text-slate-400 hover:text-slate-600"
                    >
                      ✕
                    </button>
                  </div>
                  <NodeConfigPanel
                    node={selectedNode}
                    meta={metaMap}
                    edges={edges}
                    workflowId={workflow?.id ?? ""}
                    onUpdate={onUpdateNode}
                    onBranch={onBranch}
                  />
                </div>
              ) : tab === "history" ? (
                activeExecution ? (
                  <div className="min-h-0 flex-1">
                    <div className="flex items-center justify-between border-b border-slate-200 px-3 py-1.5">
                      <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Execution</span>
                      <button
                        onClick={() => setActiveExecution(null)}
                        className="text-[11px] text-slate-400 hover:text-slate-600"
                      >
                        List
                      </button>
                    </div>
                    <ExecutionView execution={activeExecution} />
                  </div>
                ) : (
                  <div className="min-h-0 flex-1">
                    <ExecutionsList workflowId={workflowId} onLoad={setActiveExecution} activeId={null} />
                  </div>
                )
              ) : (
                <div className="min-h-0 flex-1">
                  <RunPanel onRun={handleRun} running={running} result={result} />
                </div>
              )}
            </aside>
          ) : null}
        </div>
      </div>
    </ReactFlowProvider>
  );
}