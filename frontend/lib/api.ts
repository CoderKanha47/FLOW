import type {
  ExecutionDetail,
  ExecutionSummary,
  NodeTypeMeta,
  Workflow,
} from "./types";

const TOKEN_KEY = "flow_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function currentUser(): { email: string } | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("flow_user");
  return raw ? (JSON.parse(raw) as { email: string }) : null;
}

export function setCurrentUser(email: string) {
  localStorage.setItem("flow_user", JSON.stringify({ email }));
}

const BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const parsed = JSON.parse(text);
      detail = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

export const api = {
  register: (email: string, password: string) =>
    apiFetch<{ id: string; email: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    apiFetch<{ access_token: string; token_type: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => apiFetch<{ id: string; email: string }>("/api/auth/me"),

  nodeTypes: () => apiFetch<NodeTypeMeta[]>("/api/workflows/node-types"),

  listWorkflows: () => apiFetch<Workflow[]>("/api/workflows"),
  getWorkflow: (id: string) => apiFetch<Workflow>(`/api/workflows/${id}`),
  createWorkflow: (wf: Partial<Workflow>) =>
    apiFetch<Workflow>("/api/workflows", { method: "POST", body: JSON.stringify(wf) }),
  updateWorkflow: (id: string, wf: Partial<Workflow>) =>
    apiFetch<Workflow>(`/api/workflows/${id}`, { method: "PUT", body: JSON.stringify(wf) }),
  deleteWorkflow: (id: string) =>
    apiFetch<void>(`/api/workflows/${id}`, { method: "DELETE" }),

  runWorkflow: (id: string, input: Record<string, unknown>) =>
    apiFetch<ExecutionDetail>(`/api/workflows/${id}/run`, {
      method: "POST",
      body: JSON.stringify({ input }),
    }),
  listExecutions: (workflowId: string) =>
    apiFetch<ExecutionSummary[]>(`/api/workflows/${workflowId}/executions`),
  getExecution: (executionId: string) =>
    apiFetch<ExecutionDetail>(`/api/executions/${executionId}`),
};