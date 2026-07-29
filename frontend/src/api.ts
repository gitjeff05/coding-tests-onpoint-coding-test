import type { Level, Node, TreeNode } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
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
