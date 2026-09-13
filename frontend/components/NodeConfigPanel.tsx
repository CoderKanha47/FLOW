"use client";

import { useEffect, useState } from "react";

import { nodeVisual } from "@/lib/nodeVisuals";
import type { NodeFieldMeta, NodeTypeMeta } from "@/lib/types";
import type { RFEdge, RFNode } from "@/lib/flow";

interface NodeConfigPanelProps {
  node: RFNode | null;
  meta: Map<string, NodeTypeMeta>;
  edges: unknown[];
  workflowId: string;
  onUpdate: (id: string, patch: { name?: string; config?: Record<string, unknown> }) => void;
  onBranch: (edgeId: string, branch: string) => void;
}

export default function NodeConfigPanel({ node, meta, edges, workflowId, onUpdate, onBranch }: NodeConfigPanelProps) {
  if (!node) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-sm text-slate-400">
        Select a node to configure it.
      </div>
    );
  }

  const nodeMeta = meta.get(node.data.wfType);
  const outgoing = (edges as RFEdge[]).filter((e) => e.source === node.id);
  const visual = nodeVisual(node.data.wfType);
  const Icon = visual.icon;

  return (
    <div className="flex h-full flex-col overflow-y-auto p-3">
      <div className="mb-3 flex items-center gap-2.5">
        <span className="flex h-8 w-8 items-center justify-center rounded-md" style={{ backgroundColor: visual.color }}>
          <Icon className="h-4 w-4 text-white" strokeWidth={2.2} />
        </span>
        <div>
          <div className="text-sm font-semibold text-slate-800">{nodeMeta?.label || node.data.wfType}</div>
          <div className="font-mono text-[10px] text-slate-400">{node.data.name || node.data.wfType}</div>
        </div>
      </div>

      {node.data.wfType === "webhook" ? (
        <div className="mb-4">
          <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate-400">
            Webhook endpoint
          </label>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-2">
            <div className="flex items-center gap-1.5">
              <span className="shrink-0 rounded bg-cyan-600 px-1.5 py-0.5 text-[9px] font-bold text-white">POST</span>
              <code className="flex-1 truncate font-mono text-[10px] text-slate-700">
                {workflowUrl(workflowId)}
              </code>
              <WebhookCopy url={workflowUrl(workflowId)} />
            </div>
          </div>
          <p className="mt-1 text-[10px] text-slate-400">Call this URL with a JSON body. Publish the workflow to activate it.</p>
        </div>
      ) : null}

      <label className="mb-1 text-[11px] font-medium uppercase tracking-wide text-slate-400">
        Node name
      </label>
      <input
        className="mb-4 rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-800 outline-none focus:border-cyan-500"
        value={node.data.name || ""}
        onChange={(e) => onUpdate(node.id, { name: e.target.value })}
        placeholder="Untitled node"
      />

      {(nodeMeta?.fields || []).map((field) => (
        <FieldEditor
          key={field.key}
          field={field}
          value={node.data.config?.[field.key]}
          onChange={(v) => onUpdate(node.id, { config: { ...(node.data.config || {}), [field.key]: v } })}
        />
      ))}

      {outgoing.length > 0 ? (
        <div className="mb-3">
          <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate-400">
            Outgoing edges
          </label>
          <div className="flex flex-col gap-1">
            {outgoing.map((e) => (
              <div key={e.id} className="flex items-center gap-2 rounded border border-slate-200 bg-white px-2 py-1">
                <span className="flex-1 truncate text-[11px] text-slate-500">→ {e.target.slice(0, 14)}</span>
                <input
                  className="w-24 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[11px] text-slate-700 outline-none focus:border-cyan-500"
                  placeholder="branch (e.g. true)"
                  value={e.branch ?? ""}
                  onChange={(ev) => onBranch(e.id, ev.target.value)}
                />
              </div>
            ))}
          </div>
          <p className="mt-1 text-[10px] text-slate-400">
            For Condition nodes, set branches <code>true</code>/<code>false</code>.
          </p>
        </div>
      ) : null}

      <div className="mt-3 border-t border-slate-100 pt-2 text-[10px] leading-relaxed text-slate-400">
        {nodeMeta?.description || ""}
      </div>
    </div>
  );
}

function FieldEditor({
  field,
  value,
  onChange,
}: {
  field: NodeFieldMeta;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  return (
    <div className="mb-3">
      <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate-400">
        {field.label}
      </label>
      <EditorControl field={field} value={value} onChange={onChange} />
      {field.help ? <div className="mt-1 text-[10px] leading-relaxed text-slate-400">{field.help}</div> : null}
    </div>
  );
}

function EditorControl({
  field,
  value,
  onChange,
}: {
  field: NodeFieldMeta;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const base =
    "w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-800 outline-none focus:border-cyan-500";
  switch (field.type) {
    case "textarea":
      return (
        <textarea
          rows={3}
          className={`${base} font-mono text-xs`}
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
        />
      );
    case "json":
      return <JsonEditor field={field} value={value} onChange={onChange} />;
    case "number":
      return (
        <input
          type="number"
          className={base}
          value={value == null ? "" : String(value)}
          onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
          placeholder={field.placeholder}
        />
      );
    case "boolean":
      return (
        <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            className="h-4 w-4 accent-cyan-500"
            checked={Boolean(value ?? field.default)}
            onChange={(e) => onChange(e.target.checked)}
          />
          Enabled
        </label>
      );
    case "select":
      return (
        <select
          className={base}
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
        >
          {field.options?.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      );
    default:
      return (
        <input
          type={field.secret ? "password" : "text"}
          className={`${base} font-mono text-xs`}
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
        />
      );
  }
}

function JsonEditor({
  field,
  value,
  onChange,
}: {
  field: NodeFieldMeta;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const [draft, setDraft] = useState(initial( value));

  useEffect(() => {
    const next = JSON.stringify(value ?? null);
    if (next !== JSON.stringify(tryParse(draft))) {
      setDraft(initial(value));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <textarea
      rows={4}
      className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 font-mono text-xs text-slate-800 outline-none focus:border-cyan-500"
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => {
        const parsed = tryParse(draft);
        if (parsed !== undefined) {
          onChange(parsed);
        }
      }}
      placeholder={field.placeholder || "{}"}
    />
  );

  function initial(v: unknown): string {
    if (typeof v === "string") return v;
    return JSON.stringify(v ?? null, null, 2);
  }
}

function tryParse(input: string): unknown | undefined {
  const trimmed = input.trim();
  if (!trimmed) return undefined;
  try {
    return JSON.parse(trimmed);
  } catch {
    return undefined;
  }
}

function workflowUrl(workflowId: string): string {
  return `${window.location.origin}/api/webhooks/${workflowId}`;
}

function WebhookCopy({ url }: { url: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      onClick={async () => {
        const ok = await copyText(url);
        if (ok) {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        }
      }}
      className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium transition-colors ${
        copied
          ? "border-emerald-300 bg-emerald-50 text-emerald-600"
          : "border-slate-300 bg-white text-slate-600 hover:bg-slate-100"
      }`}
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

async function copyText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // fall through to the execCommand fallback below
  }

  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "0";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    ta.setSelectionRange(0, text.length);
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}