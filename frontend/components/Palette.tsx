"use client";

import { useMemo } from "react";

import { categoryColor } from "@/lib/flow";
import { nodeVisual } from "@/lib/nodeVisuals";
import type { NodeTypeMeta } from "@/lib/types";

interface PaletteProps {
  meta: NodeTypeMeta[];
  onPick?: (type: string) => void;
}

export default function Palette({ meta, onPick }: PaletteProps) {
  const groups = useMemo(() => {
    const map = new Map<string, NodeTypeMeta[]>();
    for (const m of meta) {
      if (!map.has(m.category)) map.set(m.category, []);
      map.get(m.category)!.push(m);
    }
    return Array.from(map.entries());
  }, [meta]);

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      <h2 className="px-1 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Nodes
      </h2>
      {groups.map(([category, items]) => (
        <div key={category}>
          <div
            className="mb-1 px-1 text-[10px] font-medium uppercase tracking-wide"
            style={{ color: categoryColor(category) }}
          >
            {category}
          </div>
          <div className="flex flex-col gap-1">
            {items.map((n) => {
              const visual = nodeVisual(n.type);
              const Icon = visual.icon;
              return (
                <button
                  key={n.type}
                  draggable={!onPick}
                  onDragStart={(e) => {
                    e.dataTransfer.setData("application/flow-node", n.type);
                    e.dataTransfer.effectAllowed = "move";
                  }}
                  onClick={onPick ? () => onPick(n.type) : undefined}
                  className="group flex w-full cursor-pointer items-center gap-2 rounded-md border border-slate-200 bg-white px-2 py-1.5 text-left text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50 active:cursor-grabbing"
                >
                  <span
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded"
                    style={{ backgroundColor: visual.color }}
                  >
                    <Icon className="h-3.5 w-3.5 text-white" strokeWidth={2.2} />
                  </span>
                  <div className="min-w-0">
                    <div className="truncate text-xs font-medium">{n.label}</div>
                    <div className="truncate text-[10px] text-slate-400">{n.description || n.type}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}