import {
  CalendarClock,
  Database,
  GitBranch,
  Globe,
  NotebookText,
  Pencil,
  Rocket,
  Sparkles,
  Webhook,
  type LucideIcon,
} from "lucide-react";

export interface NodeVisual {
  color: string;
  icon: LucideIcon;
}

const VISUALS: Record<string, NodeVisual> = {
  manual_trigger: { color: "#3b82f6", icon: Rocket },
  webhook: { color: "#3b82f6", icon: Webhook },
  schedule_trigger: { color: "#3b82f6", icon: CalendarClock },
  transform: { color: "#f59e0b", icon: Pencil },
  condition: { color: "#ef4444", icon: GitBranch },
  http_request: { color: "#10b981", icon: Globe },
  database: { color: "#0ea5e9", icon: Database },
  llm: { color: "#8b5cf6", icon: Sparkles },
  log: { color: "#64748b", icon: NotebookText },
};

const DEFAULT_VISUAL: NodeVisual = { color: "#64748b", icon: NotebookText };

export function nodeVisual(type: string): NodeVisual {
  return VISUALS[type] ?? DEFAULT_VISUAL;
}