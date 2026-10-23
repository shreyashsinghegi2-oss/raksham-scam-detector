import { bandsFor } from "../lib/bands";
import type { Entry, Health } from "../lib/types";

const FALLBACK = { balanced: 0.71, strict: 0.93 };
const COLOR = Object.fromEntries(bandsFor(FALLBACK).map((b) => [b.name, b.color]));
const ago = (t: number) => {
  const s = Math.max(1, Math.round((Date.now() - t) / 1000));
  return s < 60 ? `${s}s ago` : s < 3600 ? `${Math.round(s / 60)}m ago` : s < 86400 ? `${Math.round(s / 3600)}h ago` : `${Math.round(s / 86400)}d ago`;
};

type Props = { entries: Entry[]; onPick: (e: Entry) => void; onClear: () => void; health: Health | null };

export function History({ entries, onPick, onClear }: Props) {
  return (
    <section aria-label="Analysis history">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="label">Analysis history</h2>
        {entries.length > 0 && <button type="button" onClick={onClear} className="text-xs text-zinc-500 transition hover:text-zinc-200">Clear</button>}
      </div>
      {entries.length === 0 ? (
        <p className="py-4 text-sm text-zinc-600">Nothing checked yet. Your recent checks stay in this browser.</p>
      ) : (
        <ul className="max-h-[330px] divide-y divide-white/[0.06] overflow-y-auto">
          {entries.map((e) => (
            <li key={e.id}>
              <button type="button" onClick={() => onPick(e)} className="group -mx-2 flex w-[calc(100%+1rem)] items-center gap-3 rounded-md px-2 py-3 text-left transition hover:bg-white/[0.04]">
                <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: COLOR[e.band] }} aria-hidden="true" />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm text-zinc-300 transition group-hover:text-white">{e.text.replace(/\s+/g, " ")}</span>
                  <span className="text-xs text-zinc-600">{e.band} risk · {ago(e.at)}{e.type ? ` · ${e.type.replaceAll("_", " ")}` : ""}</span>
                </span>
                <span className="tnum text-sm font-medium" style={{ color: COLOR[e.band] }}>{(e.p * 100).toFixed(1)}%</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
