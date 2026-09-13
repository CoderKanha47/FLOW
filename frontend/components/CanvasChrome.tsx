"use client";

import { useReactFlow } from "@xyflow/react";
import {
  ChevronDown,
  Lock,
  LogOut,
  Maximize2,
  Menu,
  Minus,
  Moon,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  Workflow as WorkflowIcon,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import Palette from "@/components/Palette";
import { createNodeData, type RFNode } from "@/lib/flow";
import type { NodeTypeMeta } from "@/lib/types";
import { userProfile } from "@/lib/user";

interface CanvasChromeProps {
  meta: NodeTypeMeta[];
  locked: boolean;
  dark: boolean;
  collapsed: boolean;
  onAddNode: (node: RFNode) => void;
  onToggleLock: () => void;
  onToggleDark: () => void;
  onToggleInspector: () => void;
}

export default function CanvasChrome({
  meta,
  locked,
  dark,
  collapsed,
  onAddNode,
  onToggleLock,
  onToggleDark,
  onToggleInspector,
}: CanvasChromeProps) {
  return (
    <div className="pointer-events-none absolute inset-0 z-10 select-none">
      <CanvasHeader dark={dark} onToggleDark={onToggleDark} />
      <ZoomControls dark={dark} locked={locked} collapsed={collapsed} onToggleLock={onToggleLock} onToggleInspector={onToggleInspector} />
      <AddNodeButton
        dark={dark}
        meta={meta}
        onAddNode={(node) => {
          onAddNode(node);
        }}
      />
      <CanvasHints dark={dark} />
    </div>
  );
}

function IconButton({
  dark,
  title,
  onClick,
  children,
  active = false,
}: {
  dark: boolean;
  title: string;
  onClick?: () => void;
  children: React.ReactNode;
  active?: boolean;
}) {
  const darkCls = dark
    ? "bg-slate-800 text-slate-200 hover:bg-slate-700"
    : "bg-white text-slate-600 hover:bg-slate-100";
  return (
    <button
      title={title}
      onClick={onClick}
      className={`pointer-events-auto flex h-7 w-7 items-center justify-center rounded-full border shadow-sm transition-colors ${
        dark ? "border-slate-700" : "border-slate-200"
      } ${darkCls} ${active ? "!text-cyan-600" : ""}`}
    >
      {children}
    </button>
  );
}

function CanvasHeader({ dark, onToggleDark }: { dark: boolean; onToggleDark: () => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [profile, setProfile] = useState<ReturnType<typeof userProfile>>(null);
  const frame = useRef<HTMLDivElement>(null);
  const darkCls = dark
    ? "bg-slate-800 text-slate-200 hover:bg-slate-700"
    : "bg-white text-slate-600 hover:bg-slate-100";

  useEffect(() => {
    setProfile(userProfile());
  }, []);

  return (
    <div ref={frame} className="pointer-events-auto absolute top-3 left-3 flex items-center gap-2">
      <div className="flex items-stretch overflow-hidden rounded-lg border shadow-sm border-slate-200 bg-white">
        <button
          title="Menu"
          onClick={() => setMenuOpen((o) => !o)}
          className={`flex items-center justify-center px-2.5 ${darkCls} border-r border-slate-200`}
        >
          <Menu className="h-4 w-4" />
        </button>
        <button
          title="Workspace"
          className="flex items-center gap-2 px-2.5 py-1.5"
          onClick={() => setMenuOpen((o) => !o)}
        >
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-600 text-[8px] font-bold text-white">
            {profile?.initials ?? "?"}
          </span>
          <span className="hidden flex-col items-start leading-tight sm:flex">
            <span className="text-[11px] font-semibold text-slate-700">{profile?.display ?? "Account"}</span>
            <span className="text-[9px] text-slate-400">{profile?.email ?? ""}</span>
          </span>
          <ChevronDown className="h-3 w-3 text-slate-400" />
        </button>
        <button
        title="Toggle canvas theme"
        onClick={onToggleDark}
        className={`flex items-center justify-center px-2.5 border-l border-slate-200 ${darkCls}`}
      >
        <Moon className="h-4 w-4" />
      </button>
      </div>

      {menuOpen ? (
        <div className="absolute top-11 left-0 z-20 w-52 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
          <MenuItem icon={<WorkflowIcon className="h-3.5 w-3.5" />} label="Home" href="/workflows" onClick={() => setMenuOpen(false)} />
          <MenuItem icon={<LogOut className="h-3.5 w-3.5" />} label="Sign out" href="/login" onClick={() => setMenuOpen(false)} />
        </div>
      ) : null}
    </div>
  );
}

function MenuItem({
  icon,
  label,
  href,
  disabled,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  href?: string;
  disabled?: boolean;
  onClick?: () => void;
}) {
  const inner = (
    <span className="flex items-center gap-2 px-3 py-1.5 text-xs text-slate-600">
      {icon}
      {label}
    </span>
  );
  const cls = `block w-full text-left ${disabled ? "pointer-events-none opacity-40" : "hover:bg-slate-50"}`;
  if (href) {
    return (
      <a href={href} className={cls} onClick={onClick}>
        {inner}
      </a>
    );
  }
  return (
    <span className={cls} aria-hidden={disabled}>
      {inner}
    </span>
  );
}

function ZoomControls({
  dark,
  locked,
  collapsed,
  onToggleLock,
  onToggleInspector,
}: {
  dark: boolean;
  locked: boolean;
  collapsed: boolean;
  onToggleLock: () => void;
  onToggleInspector: () => void;
}) {
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  return (
    <div className="pointer-events-auto absolute top-3 right-3 flex flex-col items-center gap-1.5">
      <div className="flex flex-col items-center rounded-full border border-slate-200 bg-white p-1 shadow-sm">
        <button
          title="Zoom in"
          onClick={() => zoomIn({ duration: 150 })}
          className={`flex h-7 w-7 items-center justify-center rounded-full ${dark ? "hover:bg-slate-100" : "hover:bg-slate-100"} text-slate-500`}
        >
          <Plus className="h-4 w-4" />
        </button>
        <button
          title="Zoom out"
          onClick={() => zoomOut({ duration: 150 })}
          className="flex h-7 w-7 items-center justify-center rounded-full text-slate-500 hover:bg-slate-100"
        >
          <Minus className="h-4 w-4" />
        </button>
      </div>
      <IconButton dark={dark} title={collapsed ? "Expand inspector" : "Collapse inspector"} onClick={onToggleInspector}>
        {collapsed ? <PanelRightOpen className="h-4 w-4" /> : <PanelRightClose className="h-4 w-4" />}
      </IconButton>
      <IconButton dark={dark} title="Fit to view" onClick={() => fitView({ padding: 0.2, duration: 300 })}>
        <Maximize2 className="h-4 w-4" />
      </IconButton>
      <IconButton dark={dark} title={locked ? "Unlock canvas" : "Lock canvas"} onClick={onToggleLock} active={locked}>
        <Lock className="h-4 w-4" />
      </IconButton>
    </div>
  );
}

function AddNodeButton({
  dark,
  meta,
  onAddNode,
}: {
  dark: boolean;
  meta: NodeTypeMeta[];
  onAddNode: (node: RFNode) => void;
}) {
  const [open, setOpen] = useState(false);
  const { screenToFlowPosition } = useReactFlow();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "+" && e.key !== "=") return;
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      setOpen((o) => !o);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const pick = (type: string) => {
    const m = meta.find((x) => x.type === type);
    const el = document.getElementById("flow-canvas");
    const cx = el ? el.clientWidth / 2 : 260;
    const cy = el ? el.clientHeight / 2 : 180;
    const position = screenToFlowPosition({ x: cx, y: cy });
    onAddNode({
      id: `${type}_${Date.now().toString(36)}`,
      type: "workflow",
      position: { x: position.x - 82, y: position.y - 26 },
      width: 164,
      data: createNodeData(type, m?.label || type),
    } as RFNode);
    setOpen(false);
  };

  return (
    <div className="pointer-events-auto absolute bottom-6 left-1/2 -translate-x-1/2">
      {open ? (
        <div className="absolute bottom-12 left-1/2 z-20 h-[420px] w-72 -translate-x-1/2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
          <Palette meta={meta} onPick={pick} />
        </div>
      ) : null}
      <button
        title="Add node"
        onClick={() => setOpen((o) => !o)}
        className={`flex h-11 w-11 items-center justify-center rounded-full border shadow-md transition-colors ${
          dark ? "border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700" : "border-slate-200 bg-white text-slate-700 shadow-slate-200 hover:bg-slate-50"
        }`}
      >
        <Plus className="h-5 w-5" strokeWidth={2.4} />
      </button>
    </div>
  );
}

function CanvasHints({ dark }: { dark: boolean }) {
  const chip = dark
    ? "bg-slate-800/80 border-slate-600 text-slate-200"
    : "bg-white/80 border-slate-200 text-slate-600";
  const key = dark
    ? "bg-slate-700 text-slate-100 border-slate-500"
    : "bg-slate-100 text-slate-600 border-slate-200";

  return (
    <div className="pointer-events-auto absolute right-5 bottom-24 flex flex-col items-end gap-1.5">
      <div className={`flex items-center gap-1.5 rounded-md border px-2 py-1 shadow-sm backdrop-blur ${chip}`}>
        <kbd className={`rounded border px-1 font-mono text-[9px] font-bold ${key}`}>+</kbd>
        <span className="text-[10px]">make new node</span>
      </div>
      <div className={`flex items-center gap-1.5 rounded-md border px-2 py-1 shadow-sm backdrop-blur ${chip}`}>
        <kbd className={`rounded border px-1 font-mono text-[9px] font-bold ${key}`}>Backspace</kbd>
        <span className="text-[10px]">remove node</span>
      </div>
    </div>
  );
}