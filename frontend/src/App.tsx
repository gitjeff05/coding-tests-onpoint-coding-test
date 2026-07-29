import { useEffect, useState } from "react";
import { createNode, getTree } from "./api";
import HierarchyNode from "./HierarchyNode";
import type { TreeNode } from "./types";
import "./App.css";

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
    <div className="app">
      <h1>SKU Hierarchy</h1>
      <p className="subtitle">Location &gt; Department &gt; Category &gt; SubCategory</p>

      <div className="node-row add-row">
        <input
          placeholder="New location name"
          value={newLocation}
          onChange={(e) => setNewLocation(e.target.value)}
        />
        <button onClick={addLocation}>+ location</button>
      </div>

      {error && <div className="node-error">{error}</div>}
      {loading && <p>Loading...</p>}

      <ul className="tree-root">
        {tree.map((node) => (
          <HierarchyNode key={node.id} node={node} onChange={reload} />
        ))}
      </ul>
    </div>
  );
}
