import { useState } from "react";
import { createNode, deleteNode, updateNode } from "./api";
import { CHILD_LEVEL, type TreeNode } from "./types";
import { LEVEL_BADGE, button, input } from "./ui";

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
    <li className="py-0.5">
      <div className="flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-slate-50">
        <span
          className={`w-24 shrink-0 rounded-full px-2 py-0.5 text-center text-[10px] font-semibold uppercase tracking-wide ${LEVEL_BADGE[node.level]}`}
        >
          {node.level}
        </span>

        {editing ? (
          <>
            <input
              className={`${input} flex-1`}
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
            <button className={button.primary} onClick={saveEdit}>
              Save
            </button>
            <button
              className={button.neutral}
              onClick={() => {
                setEditing(false);
                setName(node.name);
              }}
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <span className="flex-1 text-sm text-slate-800">{node.name}</span>
            <div className="flex gap-1.5">
              <button className={button.neutral} onClick={() => setEditing(true)}>
                Edit
              </button>
              {childLevel && (
                <button className={button.add} onClick={() => setAdding((v) => !v)}>
                  + {childLevel}
                </button>
              )}
              <button className={button.danger} onClick={remove}>
                Delete
              </button>
            </div>
          </>
        )}
      </div>

      {adding && childLevel && (
        <div className="ml-9 flex items-center gap-2 py-1.5">
          <input
            className={`${input} flex-1`}
            placeholder={`New ${childLevel} name`}
            value={childName}
            onChange={(e) => setChildName(e.target.value)}
            autoFocus
          />
          <button className={button.primary} onClick={addChild}>
            Add
          </button>
          <button className={button.neutral} onClick={() => setAdding(false)}>
            Cancel
          </button>
        </div>
      )}

      {error && (
        <div className="ml-9 mt-1 rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-xs text-red-700">
          {error}
        </div>
      )}

      {node.children.length > 0 && (
        <ul className="ml-6 border-l border-slate-200 pl-3">
          {node.children.map((child) => (
            <HierarchyNode key={child.id} node={child} onChange={onChange} />
          ))}
        </ul>
      )}
    </li>
  );
}
