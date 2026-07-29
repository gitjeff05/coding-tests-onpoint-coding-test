export type Level = "location" | "department" | "category" | "subcategory";

export const CHILD_LEVEL: Record<Level, Level | null> = {
  location: "department",
  department: "category",
  category: "subcategory",
  subcategory: null,
};

export interface Node {
  id: number;
  level: Level;
  name: string;
  parent_id: number | null;
}

export interface TreeNode extends Node {
  children: TreeNode[];
}
