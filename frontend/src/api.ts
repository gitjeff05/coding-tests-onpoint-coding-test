import { getToken } from "./auth";
import type { Level, Node, TreeNode } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export class UnauthorizedError extends Error {}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = body.detail ?? `request failed: ${res.status}`;
    if (res.status === 401) throw new UnauthorizedError(message);
    throw new Error(message);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function login(username: string, password: string): Promise<{ access_token: string; token_type: string }> {
  return request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
}

export function getTree(): Promise<TreeNode[]> {
  return request("/api/tree");
}

export function createNode(node: { level: Level; name: string; parent_id: number | null }): Promise<Node> {
  return request("/api/nodes", { method: "POST", body: JSON.stringify(node) });
}

export function updateNode(id: number, update: { name: string }): Promise<Node> {
  return request(`/api/nodes/${id}`, { method: "PUT", body: JSON.stringify(update) });
}

export function deleteNode(id: number): Promise<void> {
  return request(`/api/nodes/${id}`, { method: "DELETE" });
}
