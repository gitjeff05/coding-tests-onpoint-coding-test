import { useState } from "react";
import { createNode, deleteNode, updateNode } from "./api";
import { CHILD_LEVEL, type TreeNode } from "./types";

interface Props {
  node: TreeNode;
  onChange: () => void;
}

export default function HierarchyNode({ node, onChange }: Props) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(node.name);
  const [adding, setAdding] = useState(false);
  const [childName, setChildName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const childLevel = CHILD_LEVEL[node.level];

  async function saveEdit() {
    try {
      await updateNode(node.id, { name });
      setEditing(false);
      onChange();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function remove() {
    if (!confirm(`Delete "${node.name}" and everything under it?`)) return;
    try {
      await deleteNode(node.id);
      onChange();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function addChild() {
    if (!childLevel || !childName.trim()) return;
    try {
      await createNode({ level: childLevel, name: childName.trim(), parent_id: node.id });
      setChildName("");
      setAdding(false);
      onChange();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <li className="node">
      <div className="node-row">
        <span className="node-level">{node.level}</span>
        {editing ? (
          <>
            <input value={name} onChange={(e) => setName(e.target.value)} autoFocus />
            <button onClick={saveEdit}>Save</button>
            <button onClick={() => { setEditing(false); setName(node.name); }}>Cancel</button>
          </>
        ) : (
          <>
            <span className="node-name">{node.name}</span>
            <button onClick={() => setEditing(true)}>Edit</button>
            {childLevel && <button onClick={() => setAdding((v) => !v)}>+ {childLevel}</button>}
            <button onClick={remove}>Delete</button>
          </>
        )}
      </div>

      {adding && childLevel && (
        <div className="node-row add-row">
          <input
            placeholder={`New ${childLevel} name`}
            value={childName}
            onChange={(e) => setChildName(e.target.value)}
            autoFocus
          />
          <button onClick={addChild}>Add</button>
          <button onClick={() => setAdding(false)}>Cancel</button>
        </div>
      )}

      {error && <div className="node-error">{error}</div>}

      {node.children.length > 0 && (
        <ul>
          {node.children.map((child) => (
            <HierarchyNode key={child.id} node={child} onChange={onChange} />
          ))}
        </ul>
      )}
    </li>
  );
}
