import { useEffect, useState } from "react";
import { createNode, getTree } from "./api";
import HierarchyNode from "./HierarchyNode";
import type { TreeNode } from "./types";
import { button, input } from "./ui";

export default function App() {
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [newLocation, setNewLocation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function reload() {
    try {
      setTree(await getTree());
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, []);

  async function addLocation() {
    if (!newLocation.trim()) return;
    try {
      await createNode({ level: "location", name: newLocation.trim(), parent_id: null });
      setNewLocation("");
      reload();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto max-w-4xl px-6 py-10">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">SKU Hierarchy</h1>
          <p className="text-sm text-slate-500">
            Location &gt; Department &gt; Category &gt; SubCategory
          </p>
        </header>

        <div className="mb-6 flex items-center gap-2">
          <input
            className={`${input} w-64`}
            placeholder="New location name"
            value={newLocation}
            onChange={(e) => setNewLocation(e.target.value)}
          />
          <button className={button.primary} onClick={addLocation}>
            + location
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        {loading && <p className="text-sm text-slate-500">Loading...</p>}

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <ul>
            {tree.map((node) => (
              <HierarchyNode key={node.id} node={node} onChange={reload} />
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
