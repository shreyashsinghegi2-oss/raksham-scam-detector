import { useCallback, useEffect, useState } from "react";
import type { Entry } from "./types";

const KEY = "raksham-history-v2";
const MAX = 20;

function load(): Entry[] {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(raw) ? raw.filter((e) => e && typeof e.p === "number" && typeof e.text === "string").slice(0, MAX) : [];
  } catch { return []; }
}

/** Recent checks, kept in this browser only. Nothing here is sent to the server. */
export function useHistory() {
  const [entries, setEntries] = useState<Entry[]>(load);
  useEffect(() => { try { localStorage.setItem(KEY, JSON.stringify(entries)); } catch { /* storage unavailable */ } }, [entries]);
  const add = useCallback((e: Omit<Entry, "id" | "at">) => setEntries((cur) => [{ ...e, id: Date.now() + Math.random(), at: Date.now() }, ...cur].slice(0, MAX)), []);
  const clear = useCallback(() => setEntries([]), []);
  return { entries, add, clear };
}
