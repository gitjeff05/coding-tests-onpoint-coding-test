import type { Level } from "./types";

export const LEVEL_BADGE: Record<Level, string> = {
  location: "bg-indigo-100 text-indigo-700",
  department: "bg-sky-100 text-sky-700",
  category: "bg-emerald-100 text-emerald-700",
  subcategory: "bg-amber-100 text-amber-700",
};

const btn = "rounded-md border px-2 py-1 text-xs font-medium transition-colors";

export const button = {
  primary: `${btn} border-blue-600 bg-blue-600 text-white hover:bg-blue-700`,
  neutral: `${btn} border-slate-300 text-slate-600 hover:bg-slate-100`,
  add: `${btn} border-blue-300 text-blue-600 hover:bg-blue-50`,
  danger: `${btn} border-red-300 text-red-600 hover:bg-red-50`,
};

export const input =
  "rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";
